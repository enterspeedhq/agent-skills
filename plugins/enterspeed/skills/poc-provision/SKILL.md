---
name: poc-provision
description: "Provision a PoC requested in the #poc-register Slack channel. Creates the Azure resource group (or a customer subscription), a budget, a capped Log Analytics workspace with Application Insights, Terraform state storage with Entra auth, a pim- Entra group with PIM for Groups (eligible membership, one activation), and a GitHub repo with Secret Protection, then logs the access and replies in the request thread. Use when the user says 'provision the PoC', 'set up the PoC from poc-register', 'opsæt PoC'en', 'sæt BRIM op', 'handle the poc-register request', 'poc-provision', or pastes a link to a #poc-register message. Not for PoCs that need production access, and not for changes to the platform's own infrastructure."
---

# PoC provision

You turn a request from #poc-register into a working PoC environment: an Azure scope the requester can deploy to through PIM, a budget, somewhere to send logs, shared Terraform state, a GitHub repo, a log entry and a reply in the thread. The requests are written by the **poc-request** skill (a Claude organisation skill in claude.ai), so they follow a fixed template.

This is the v0 of the PoC framework: the requester deploys **locally after activating PIM**. Terraform state, the OIDC deploy identity and the shared GitHub workflow are not part of v0, so don't set them up.

Every step that creates something is shown to the user first, and only run once they say yes. Run the commands one at a time and show the output.

---

## Prerequisites

Check these before Step 1 and stop with a clear message if one is missing:

- **Azure CLI**, logged in to the Enterspeed tenant: `az account show`. If it's missing: https://learn.microsoft.com/cli/azure/install-azure-cli
- **GitHub CLI** with `repo` scope: `gh auth status`. `admin:org` is **not** needed.
- **Python 3.8+**, for `<skill-path>/scripts/pim_role.py`.
- **Slack MCP tools**, to read the request and reply. If they're unavailable, ask the user to paste the request and give them the reply text at the end instead of posting it.
- **Rights:**
  - Owner on *Enterspeed PoC - MCA* for path A.
  - The *Azure subscription creator* role on the MCA invoice section for path B.
  - Permission to create Entra groups.
  - Permission to manage PIM for Groups (e.g. as group owner or Privileged Role Administrator) for Step 6b, which is done in the portal.

  If a command later fails with an authorisation error, stop and say which role is missing. Don't try a different route around it.

---

## Step 1: Read the request

Find the request:
- If the user gave a link, read that message.
- Otherwise, read #poc-register (find the channel with `slack_search_channels`) and ask which request to handle, if there are several without a reply in their thread.

Extract: app, customer (if any), what is to be hosted, internal people, data class, approval/DPA, end date, technology (AI, external services), and the check marks.

**Questions before you go on.** These are questions, not verdicts:
- **🛑 personal data without a DPA:** ask whether to set up the environment anyway, with the agreement that no real data goes on until the DPA is in place.
- **🔶 customer project:** ask whether a developer has been assigned. The environment can still be set up.
- **⚠️ direct LLM calls (e.g. Anthropic):** ask whether that's accepted. If it is, Step 8 applies.
- **An end date in the past or more than 180 days out:** ask for the correct date.

If the request has been changed or answered in the thread, the thread wins over the original message.

---

## Step 2: Path, names and plan

**Path:**

| The request says | Path | Azure scope for PIM |
|---|---|---|
| No customer / internal experiment | **A: Internal** | Resource group in *Enterspeed PoC - MCA* (`fa1883c7-dcfb-4e09-97b4-61455bfce7f0`) |
| A named customer | **B: Customer** | New subscription `enterspeed-cust-<customer>`. **Path B hasn't been run yet:** say so, and take it a step at a time |

**Names** (decided Nov 2026, don't invent new patterns):

| Resource | Path A | Path B |
|---|---|---|
| Subscription | – | `enterspeed-cust-<customer>` |
| Resource group | `esp-poc-<app>-rg` | `esp-poc-<customer>-<app>-rg` |
| PIM group | `pim-poc-<app>-contributor` | `pim-poc-<customer>-contributor` |
| Budget | `poc-<app>-budget` | `poc-<customer>-budget` |
| Log Analytics workspace | `esp-poc-<app>-log` | `esp-poc-<customer>-<app>-log` |
| Application Insights | `esp-poc-<app>-appi` | `esp-poc-<customer>-<app>-appi` |
| Terraform state storage account | `stpoc<app>tf<4 random>` | `stpoc<customer><app>tf<4 random>` |
| GitHub repo | `enterspeedhq/<app>` | `enterspeedhq/<customer>-<app>` |

- `<app>` and `<customer>` are lowercase kebab-case with no special characters.
- **Storage account names** must be 3–24 lowercase letters and digits and globally unique, so there are no hyphens, and the 4 random characters avoid clashes. Shorten `<customer><app>` if the name would exceed 24.
- **A `poc-` prefix on the repo name is allowed** (`enterspeedhq/poc-<app>`). Use it if the request does. No other prefixes.
- **If the request's repo name doesn't follow the table** (e.g. `internal-brim`, which poc-request once invented), point out the difference and ask which name to use.

**Tags:** `app=<app>`, `owner=<initials>`, `expires=<YYYY-MM-DD>`, `environment=poc`, `source=poc-register`, and `customer=<customer>` on path B. `owner` is the **initials** (the part of the UPN before the @), never a first name.

**Find the people:** look up each internal person in Entra, e.g. `az ad user list --filter "startswith(displayName,'<first name>')" --query "[].{name:displayName,upn:userPrincipalName,id:id}" -o table`. If there are several hits or none, ask.

**Check that nothing already exists:**
```
az group exists --subscription <sub-id> --name <rg>
az ad group list --filter "displayName eq '<pim-group>'" --query "[].id" -o tsv
gh api repos/enterspeedhq/<repo> -q .full_name
```
If something already exists, stop and ask whether to reuse it or whether this is a different PoC.

**Show the plan** as a table: path, resource group, tags, budget (amount in DKK, default 500/month, recipients: the requester and the person running the skill), logging (workspace and App Insights names, daily cap, default 0.5 GB/day), Terraform state storage account, PIM group and members, roles, end date, repo. Wait for a yes.

---

## Step 3: Azure scope

**Path A:**
```
az group create --subscription fa1883c7-dcfb-4e09-97b4-61455bfce7f0 --name <rg> --location westeurope --tags app=<app> owner=<initials> expires=<date> environment=poc source=poc-register
```
Scope for Steps 4 and 6: `/subscriptions/fa1883c7-dcfb-4e09-97b4-61455bfce7f0/resourceGroups/<rg>`. The resource providers are already registered.

**Path B (untested):**
1. Find the billing scope:
   - `az billing account list`
   - `az billing profile list --account-name <acct>`
   - `az billing invoice section list --account-name <acct> --profile-name <profile>`

   Ask which invoice section to use.
2. Create the subscription: `az extension add --name account --upgrade`, then `az account alias create --name <sub> --display-name <sub> --billing-scope <scope> --workload Production`. The subscription ID is in `az account alias show --name <sub> --query properties.subscriptionId -o tsv`. If it says the subscription is "not found" right afterwards, wait a minute and try again.
3. Tag the subscription with `az tag create --resource-id /subscriptions/<id> --tags …`, using the same tags plus `customer`.
4. Register the resource providers with `az provider register --namespace <ns> --subscription <id>`, for Microsoft.Web, Microsoft.App, Microsoft.KeyVault, Microsoft.Storage, Microsoft.OperationalInsights, Microsoft.Insights, Microsoft.ContainerRegistry and Microsoft.ManagedIdentity.
5. Create the resource group as in path A, inside the new subscription.

Scope for Steps 4 and 6: `/subscriptions/<id>` (the whole customer subscription).

---

## Step 4: Budget, logging and Terraform state

### Budget

Write the body to a temporary file in the session's scratchpad and call:
```
az rest --method put --body @<file> --url "https://management.azure.com<scope>/providers/Microsoft.Consumption/budgets/<budget-name>?api-version=2023-05-01"
```
The body:
```json
{ "properties": { "category": "Cost", "amount": 500, "timeGrain": "Monthly",
  "timePeriod": { "startDate": "<first of this month>T00:00:00Z", "endDate": "<end date>T00:00:00Z" },
  "notifications": {
    "actual80":    { "enabled": true, "operator": "GreaterThan", "threshold": 80,  "thresholdType": "Actual",     "contactEmails": ["<requester>", "<you>"] },
    "forecast100": { "enabled": true, "operator": "GreaterThan", "threshold": 100, "thresholdType": "Forecasted", "contactEmails": ["<requester>", "<you>"] } } } }
```
The billing currency is DKK. `startDate` must be the first of a month.

### Logging

Each PoC gets its own Log Analytics workspace with a **daily cap**, plus a workspace-based Application Insights. Logs stay in the PoC's own resource group, so customer PoCs aren't mixed together, and the cap means runaway logging can't eat the budget. When the cap is hit, ingestion stops until midnight UTC, which is acceptable for a PoC.

```
az monitor log-analytics workspace create --subscription <sub-id> --resource-group <rg> --workspace-name <log-name> --location westeurope --retention-time 30 --quota 0.5 --tags app=<app> owner=<initials> expires=<date> environment=poc source=poc-register
az monitor app-insights component create --subscription <sub-id> --resource-group <rg> --app <appi-name> --location westeurope --application-type web --workspace <log-name> --tags app=<app> owner=<initials> expires=<date> environment=poc source=poc-register
```
- **Extension prompt:** the Azure CLI may ask to install the `application-insights` extension the first time. Say yes, or run `az extension add --name application-insights` first.
- **If the requester has asked for Elastic serverless instead:** still create the workspace. The platform's Container Apps or App Service logs go there anyway, and Elastic is the app's own choice on top.

**How the app uses it.** This goes in the repo's `POC_ENVIRONMENT.md` (Step 7), so the build skill can wire it up:
- **Console logs without code:** point the Container Apps environment (or App Service diagnostic settings) at the workspace in the app's Terraform.
- **Traces, metrics and structured logs:** use the Azure Monitor OpenTelemetry distro (`Azure.Monitor.OpenTelemetry.AspNetCore` for .NET, `@azure/monitor-opentelemetry` for Node), with `APPLICATIONINSIGHTS_CONNECTION_STRING` as an environment variable.
- **Getting the connection string:** the app's Terraform reads it from the App Insights resource with a data source, using the name above. The connection string can only send data, not read it. Entra-only ingestion (disabling local auth) is not part of v0.

### Terraform state

Infrastructure changes need shared state with locking, otherwise two people's `terraform apply` overwrite each other, and a local state file is lost with the laptop. **Code deployments don't use the state** (`az acr build` + `az containerapp update`), so anyone with access can deploy code regardless.

The storage account allows **Entra auth only**. Shared keys are turned off, so access to the state goes through PIM like everything else, and there's no key that can leak.

```
az storage account create --subscription <sub-id> --resource-group <rg> --name <state-sa> --location westeurope --sku Standard_LRS --kind StorageV2 --min-tls-version TLS1_2 --https-only true --allow-blob-public-access false --allow-shared-key-access false --tags app=<app> owner=<initials> expires=<date> environment=poc source=poc-register purpose=terraform-state
az storage account blob-service-properties update --subscription <sub-id> --resource-group <rg> --account-name <state-sa> --enable-versioning true --enable-delete-retention true --delete-retention-days 7
az storage container-rm create --subscription <sub-id> --resource-group <rg> --storage-account <state-sa> --name tfstate --public-access off
```
- **Create the container with `container-rm`**, which goes through ARM. Then neither shared keys nor a data-plane role are needed for you.
- **Check the name first** with `az storage account check-name --name <state-sa> --query nameAvailable -o tsv`. If it says `false`, pick new random characters.
- The CLI warns that TLS1_0/TLS1_1 are retired. That's expected, since we set TLS1_2, so ignore it.
- Versioning and 7 days of soft delete mean a broken or deleted state file can be recovered.
- The PIM group's access to the state is set up in Step 6.

**The backend block for the app's Terraform** goes in the repo's `POC_ENVIRONMENT.md` (Step 7):
```hcl
terraform {
  backend "azurerm" {
    subscription_id      = "<sub-id>"
    resource_group_name  = "<rg>"
    storage_account_name = "<state-sa>"
    container_name       = "tfstate"
    key                  = "<app>.tfstate"
    use_azuread_auth     = true
  }
}
```

---

## Step 5: PIM group

The access model is **PIM for Groups**, the same as the `pim-spt-p-prod-*` groups: **the group holds the roles, and people are eligible members of the group.** The requester then activates **one thing**, their group membership, and gets every role at once. Don't make the roles themselves eligible: that makes the requester activate each role separately.

PoC groups are ordinary security groups, not role-assignable (decided Nov 2026). The roles are scoped to one resource group and time-limited, so the extra protection isn't worth the administration.

```
az ad group create --display-name <pim-group> --mail-nickname <pim-group> --description "PIM for Groups access to <rg> (PoC <app>, expires <date>, via #poc-register)" --query id -o tsv
```
- **Don't add anyone as a member with `az ad group member add`.** That gives standing access. Members are added as eligible in Step 6b.
- In zsh, don't call the variable `GID` (it's read-only). Use `GROUP_ID`, or paste the ID in directly.

---

## Step 6: Roles on the group, and eligible members

### 6a. The group's roles: active and time-bound

The group gets **active** assignments that end on the PoC's end date. Use the script, which builds the JSON in Python so the condition doesn't need escaping:
```
python3 <skill-path>/scripts/pim_role.py active <scope> <group-id> b24988ac-6180-42a0-ab88-20f7382dd24c <end-date> "PoC <app> per #poc-register request"
python3 <skill-path>/scripts/pim_role.py active <scope> <group-id> b86a8fe4-44ce-4948-aee5-eccb2c155cd7 <end-date> "PoC <app> per #poc-register request"
python3 <skill-path>/scripts/pim_role.py active <scope> <group-id> f58310d9-a9f6-439a-9e8d-f62e7b41a168 <end-date> "PoC <app> per #poc-register request" "<condition>"
python3 <skill-path>/scripts/pim_role.py active <state-sa-id> <group-id> ba92f5b4-2d11-453d-a403-e96b0029c9fe <end-date> "PoC <app> Terraform state per #poc-register request"
```
The four roles, in order:
1. Contributor
2. Key Vault Secrets Officer
3. **Role Based Access Control Administrator, constrained**
4. **Storage Blob Data Contributor scoped to the state storage account only**, not the resource group, so the app's own storage isn't opened up. `<state-sa-id>` is `/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<state-sa>`.

The condition on RBAC Administrator lets it create or delete assignments only for Key Vault Secrets User, Storage Table Data Contributor, Storage Blob Data Contributor and AcrPull:
```
((!(ActionMatches{'Microsoft.Authorization/roleAssignments/write'})) OR (@Request[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {4633458b-17de-408a-b874-0445c86b69e6, 0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3, ba92f5b4-2d11-453d-a403-e96b0029c9fe, 7f951dda-4ed3-4680-a7ca-43fe172d538d})) AND ((!(ActionMatches{'Microsoft.Authorization/roleAssignments/delete'})) OR (@Resource[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {4633458b-17de-408a-b874-0445c86b69e6, 0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3, ba92f5b4-2d11-453d-a403-e96b0029c9fe, 7f951dda-4ed3-4680-a7ca-43fe172d538d}))
```
Each call should return `"status": "Provisioned"`. If it doesn't, stop and show the error.

**Check:** without a filter, the list covers the scope and everything below it, so all four roles show up, the state role included:
```
az rest --method get --url "https://management.azure.com<scope>/providers/Microsoft.Authorization/roleAssignmentSchedules?api-version=2020-10-01" --query "value[?properties.principalId=='<group-id>'].{role:properties.expandedProperties.roleDefinition.displayName, scope:properties.scope, end:properties.endDateTime, condition:properties.condition!=null}" -o table
```
Expect four rows. The group has no members yet, so nobody has access until 6b.

### 6b. Eligible members: a manual step in the portal

**The Azure CLI can't do this.** Its token doesn't have the Graph permission for PIM for Groups (`PrivilegedEligibilitySchedule.ReadWrite.AzureADGroup`), and the call fails with 403. Ask the user to do it, and wait until they confirm:

1. Entra admin center → **Identity Governance → Privileged Identity Management → Groups**. If the group isn't listed, use **Discover groups** to bring it under PIM first.
2. Open `<pim-group>` → **Assignments → Add assignments**. Role: **Member**. Choose the people from the request. Assignment type: **Eligible**, ending on the PoC's end date.
3. Under **Settings → Member**, the first time for this group, set activation to:
   - at most 8 hours
   - Azure MFA required
   - justification required
   - no ticket and no approval

Optional alternative, if the user prefers scripting: Microsoft Graph PowerShell with `Connect-MgGraph -Scopes PrivilegedEligibilitySchedule.ReadWrite.AzureADGroup` and `New-MgIdentityGovernancePrivilegedAccessGroupEligibilityScheduleRequest`.

**Check:** ask the user to confirm that the person shows as an eligible member. Don't continue to the thread reply until they have.

---

## Step 7: GitHub

1. `gh repo create enterspeedhq/<repo> --private --description "PoC: <app> (expires <date>, via #poc-register)"`
2. Set the baseline tier: `gh api -X PATCH repos/enterspeedhq/<repo>/properties/values` with `{"properties":[{"property_name":"branch_protection_tier","value":"baseline"}]}`. The org ruleset then blocks deletion and force-push on `main`.
3. Turn on secret scanning and push protection with `gh api -X PATCH repos/enterspeedhq/<repo>`, sending `{"security_and_analysis":{"secret_scanning":{"status":"enabled"},"secret_scanning_push_protection":{"status":"enabled"}}}`. Don't use the org's code security configuration: attaching it needs `admin:org`.
4. Turn on Dependabot: `gh api -X PUT repos/enterspeedhq/<repo>/vulnerability-alerts` and `gh api -X PUT repos/enterspeedhq/<repo>/automated-security-fixes`.
5. **Repo access for the requester:**
   - Find their GitHub login among `gh api orgs/enterspeedhq/members`.
   - If they aren't there, look in `gh api orgs/enterspeedhq/invitations`. If they only have a pending invitation, access waits until they accept it, and they'll take a new GitHub Team seat. Say so, and include it in the thread reply.
   - When they're a member: `gh api -X PUT repos/enterspeedhq/<repo>/collaborators/<login> -f permission=push`.
6. **`POC_ENVIRONMENT.md` in the repo:** the technical description of the environment, for **app-platform-poc** and for developers. Not for the requester. Write it to a temporary file, show it, and commit it as the repo's first commit:
   ```
   gh api -X PUT repos/enterspeedhq/<repo>/contents/POC_ENVIRONMENT.md -f message="docs: PoC environment from poc-provision" -f content="$(base64 < <file> | tr -d '\n')"
   ```
   It must contain:
   - **Environment:** subscription (name and ID), resource group, region and end date
   - **Logging:** workspace and App Insights names, the daily cap, and how the app uses them (from Step 4)
   - **Terraform:** the backend block (from Step 4), and the fact that `terraform init` requires the group membership (`<pim-group>`) to be activated in PIM. If it gives 403, wait a few minutes. Code deployment (`az acr build` + `az containerapp update`) doesn't use the state.
   - **Access:** the PIM group and its roles, including what the RBAC Administrator condition allows
   - **Source:** a link to the request in #poc-register

   **Default branch:** the first commit gets the org's default branch name, which is `master`. Rename it to `main` straight away, because **app-platform-poc**'s CI triggers on `main`: `gh api -X POST repos/enterspeedhq/<repo>/branches/master/rename -f new_name=main`. The baseline ruleset applies to the default branch whatever it's called.

   **If the repo already exists and has content,** show the file and ask before committing it. Leave its branch name alone. If a `POC_ENVIRONMENT.md` already exists, update it rather than overwriting it unread.

---

## Step 8: Anthropic (only if direct LLM calls were accepted in Step 1)

You can't create workspaces or API keys. Tell the user that an admin needs to, in the Anthropic Console:
1. Create a workspace `poc-<app>` with a monthly spending limit.
2. Add the requester, so they can create the API key themselves.

The key goes into Key Vault after the requester activates PIM. It never goes over Slack or into Claude.

---

## Step 9: Close the loop

1. **Access Request Log:** use **access-request-log**. Fill in:
   - Assignment Type = Eligible (PIM) and the end date, with Role Requested saying "via PIM for Groups on <pim-group>"
   - Role Requested with the exact scope and the group, including Storage Blob Data Contributor on the state storage account
   - Comments with the condition, the group object ID, and a note that the eligibility was created through the PIM API

   **One row per PoC.** If the PoC already has a row (e.g. when adding resources or roles later, or for an extension), don't create a new one. Update the existing row instead: extend Role Requested, and add an "Update <date>: …" paragraph to Comments with what changed and who approved it.

   If the skill isn't available, give the user the table and say the row hasn't been added.
2. **Reply in the request thread.** Draft it in the requester's language, show it, and post it once the user says yes. **Keep it non-technical.** The requester wants to use the environment, not hear how it's built. Leave out resource names, Terraform, backend blocks and connection strings: the build skill takes care of those. It should cover:
   - that the environment is ready, and that the app gets logging and shared state automatically when it's built with **app-platform-poc**
   - how to activate access, in one sentence: Portal → PIM → My roles → **Groups** → activate `<pim-group>`. That one activation covers everything
   - the repo, and any pending org invitation
   - the budget
   - Anthropic, if relevant
   - the end date
3. **Remind** the user to put a calendar reminder 14 days before the end date. Expiry isn't automated yet.

---

## Step 10: Report and lessons learnt

Finish with a short summary of what was created, with names and IDs, and what's still open (e.g. repo access waiting on an invitation, the Anthropic workspace).

If a step failed, needed a workaround, or the path B steps turned out to differ: name it, and ask whether to update this skill with it.
