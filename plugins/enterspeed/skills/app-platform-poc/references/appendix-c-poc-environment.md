# Appendix C: Enterspeed PoC environment

Applies when the target repository has a **`POC_ENVIRONMENT.md` at its root**. That file is written by the **poc-provision** skill when a PoC is set up from #poc-register. It means an Azure environment already exists, and the person building is expected to deploy the tool there themselves, with no infra owner in between.

In that case this appendix **replaces §10's skeleton** with apply-ready Terraform for the PoC environment, and adds a code deploy script. Everything else in the blueprint is unchanged.

---

## C.1 Read `POC_ENVIRONMENT.md` first

It's the single source for everything environment-specific. **Never guess or invent these values.** Read them:

| From the file | Used for |
|---|---|
| Subscription ID, resource group, region | the provider, data sources, resource location |
| Log Analytics workspace and Application Insights names | the data sources (C.3). Don't create a second workspace |
| The Terraform `backend "azurerm"` block | copied verbatim into `providers.tf` |
| The PIM group | the README and hand-over: "activate `<group>` in PIM before `terraform` or `deploy.sh`" |
| End date | the README |

If a value is missing or the file doesn't follow this shape, **stop** and say which value is missing. Ask the user to get the environment completed through #poc-register, or to paste the value.

**Repo layout:** in a PoC repo, **the repo root is `<tool>/`** (§5). `<tool>-app/` and `<tool>-platform/` go straight into the root, next to `POC_ENVIRONMENT.md`. Don't create an extra `<tool>/` folder.

---

## C.2 What the PoC environment can and can't do

The person deploying works through a PIM group. It holds these roles on the resource group:
- **Contributor**
- **Key Vault Secrets Officer**
- **Role Based Access Control Administrator**, constrained so it can only assign Key Vault Secrets User, Storage Table Data Contributor, Storage Blob Data Contributor and AcrPull

That shapes the Terraform:

- **No new resource group.** Everything goes into the existing one, which is read with a data source.
- **Role assignments only for those four roles.** For anything else, e.g. AcrPush or Owner, `terraform apply` fails with 403. The app's managed identity gets **AcrPull** and **Key Vault Secrets User**, which is all §10 needs.
- **No resource provider registration.** Set `resource_provider_registrations = "none"`. The providers are registered, and the group can't register new ones at subscription level.
- **Database (Appendix B):** not covered by this appendix yet. If the tool has a database, generate the Postgres part as a `# TODO:` per §10.2 and say so in the hand-over. Don't guess at network posture, admin passwords or Entra admin.

---

## C.3 Terraform: `<tool>-platform/terraform/`

Instead of §10.2/§10.3, write these files. Replace `<…>` with values from `POC_ENVIRONMENT.md` and the tool's tokens (§2). Names follow `esp-poc-<app>-<type>`, where `<app>` is the resource group's app token.

**`providers.tf`**
```hcl
terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.0" }
    random  = { source = "hashicorp/random", version = "~> 3.6" }
  }
  # Copied verbatim from POC_ENVIRONMENT.md: shared state, Entra auth only.
  backend "azurerm" {
    subscription_id      = "<sub-id>"
    resource_group_name  = "<rg>"
    storage_account_name = "<state-sa>"
    container_name       = "tfstate"
    key                  = "<app>.tfstate"
    use_azuread_auth     = true
  }
}

provider "azurerm" {
  features {}
  subscription_id                 = var.subscription_id
  resource_provider_registrations = "none" # the PIM group can't register providers
}
```

**`variables.tf`**
```hcl
variable "subscription_id" { type = string }
variable "resource_group_name" { type = string }
variable "app" {
  type        = string
  description = "The PoC's app token, as in esp-poc-<app>-rg"
}
variable "log_analytics_workspace_name" { type = string }
variable "application_insights_name" { type = string }
```

**`terraform.tfvars`**. These values aren't secret, they come from `POC_ENVIRONMENT.md`, and the file is committed. Override §11's `**/terraform.tfvars` ignore for this one file with `!<tool>-platform/terraform/terraform.tfvars` in `.gitignore`.
```hcl
subscription_id              = "<sub-id>"
resource_group_name          = "<rg>"
app                          = "<app>"
log_analytics_workspace_name = "<log-name>"
application_insights_name    = "<appi-name>"
```

**`main.tf`**
```hcl
data "azurerm_client_config" "current" {}

data "azurerm_resource_group" "poc" {
  name = var.resource_group_name
}

data "azurerm_log_analytics_workspace" "poc" {
  name                = var.log_analytics_workspace_name
  resource_group_name = var.resource_group_name
}

data "azurerm_application_insights" "poc" {
  name                = var.application_insights_name
  resource_group_name = var.resource_group_name
}

resource "random_string" "suffix" {
  length  = 4
  special = false
  upper   = false
}

locals {
  location = data.azurerm_resource_group.poc.location
  tags     = data.azurerm_resource_group.poc.tags # app, owner, expires, environment, source
}

# --- Identity the API runs as -------------------------------------------------
resource "azurerm_user_assigned_identity" "api" {
  name                = "esp-poc-${var.app}-id"
  resource_group_name = var.resource_group_name
  location            = local.location
  tags                = local.tags
}

# --- Registry: the image is pushed by deploy.sh, not by Terraform -------------
resource "azurerm_container_registry" "acr" {
  name                = "acrpoc${replace(var.app, "-", "")}${random_string.suffix.result}"
  resource_group_name = var.resource_group_name
  location            = local.location
  sku                 = "Basic"
  admin_enabled       = false # pulls use the managed identity, never a password
  tags                = local.tags
}

resource "azurerm_role_assignment" "api_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull" # allowed by the PIM group's RBAC condition
  principal_id         = azurerm_user_assigned_identity.api.principal_id
}

# --- Key Vault: Terraform creates it; secret values are set outside Terraform -
resource "azurerm_key_vault" "kv" {
  name                       = "kv-poc-${substr(replace(var.app, "-", ""), 0, 12)}-${random_string.suffix.result}"
  resource_group_name        = var.resource_group_name
  location                   = local.location
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  rbac_authorization_enabled = true
  purge_protection_enabled   = false # a PoC must be deletable when it expires
  tags                       = local.tags
}

resource "azurerm_role_assignment" "api_kv_secrets_user" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets User" # allowed by the RBAC condition
  principal_id         = azurerm_user_assigned_identity.api.principal_id
}

# --- Container Apps: logs go to the PoC's capped workspace --------------------
resource "azurerm_container_app_environment" "env" {
  name                       = "esp-poc-${var.app}-cae"
  resource_group_name        = var.resource_group_name
  location                   = local.location
  log_analytics_workspace_id = data.azurerm_log_analytics_workspace.poc.id
  tags                       = local.tags
}

resource "azurerm_static_web_app" "web" {
  name                = "esp-poc-${var.app}-web"
  resource_group_name = var.resource_group_name
  location            = local.location
  sku_tier            = "Free"
  sku_size            = "Free"
  tags                = local.tags
}

resource "azurerm_container_app" "api" {
  name                         = "esp-poc-${var.app}-api"
  resource_group_name          = var.resource_group_name
  container_app_environment_id = azurerm_container_app_environment.env.id
  revision_mode                = "Single"
  tags                         = local.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.api.id]
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.api.id
  }

  secret {
    name  = "appinsights-connection-string"
    value = data.azurerm_application_insights.poc.connection_string
  }

  ingress {
    external_enabled = true
    target_port      = 8080
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 0 # scale to zero: a PoC costs nothing when idle
    max_replicas = 1
    container {
      name   = "api"
      image  = "mcr.microsoft.com/k8se/quickstart:latest" # placeholder until deploy.sh pushes the real image
      cpu    = 0.25
      memory = "0.5Gi"
      env {
        name  = "ASPNETCORE_ENVIRONMENT"
        value = "Production"
      }
      env {
        name  = "Cors__AllowedOrigin"
        value = "https://${azurerm_static_web_app.web.default_host_name}"
      }
      env {
        name        = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        secret_name = "appinsights-connection-string"
      }
    }
  }

  lifecycle {
    # deploy.sh rolls out new images; a later apply must not roll them back (§10).
    ignore_changes = [template[0].container[0].image]
  }

  depends_on = [azurerm_role_assignment.api_acr_pull]
}
```

**`outputs.tf`**
```hcl
output "acr_name" { value = azurerm_container_registry.acr.name }
output "container_app_name" { value = azurerm_container_app.api.name }
output "api_url" { value = "https://${azurerm_container_app.api.ingress[0].fqdn}" }
output "static_web_app_name" { value = azurerm_static_web_app.web.name }
output "frontend_url" { value = "https://${azurerm_static_web_app.web.default_host_name}" }
output "key_vault_name" { value = azurerm_key_vault.kv.name }
```

Notes:
- **The placeholder image** listens on port 80 rather than 8080, so the first revision is unhealthy until `deploy.sh` has run once. That's expected.
- **Secrets the tool needs** (e.g. an LLM API key) go in Key Vault by hand after PIM activation, and are referenced from the Container App as Key Vault secrets via the managed identity. They never go in `terraform.tfvars` or state.
- **Auth (Appendix A):** the SWA and the Container App are different sites, so §10's same-site cookie note applies. Linking the Container App as the SWA backend requires the SWA Standard plan. Flag it in the hand-over rather than switching plan unasked.

---

## C.4 Code deploy: `deploy.sh` at the repo root

Code deploys **don't use Terraform**, so anyone with the PIM group activated can run one without touching the state. The script reads names from `terraform output`. That needs read access to the state, which the PIM group has.

```bash
#!/usr/bin/env bash
# Deploys the current commit's code to the PoC environment.
# Prereq: activate the PIM group (see POC_ENVIRONMENT.md), `az login`, `terraform init` done once.
set -euo pipefail
cd "$(dirname "$0")"

TF="<tool>-platform/terraform"
ACR=$(terraform -chdir="$TF" output -raw acr_name)
APP=$(terraform -chdir="$TF" output -raw container_app_name)
SWA=$(terraform -chdir="$TF" output -raw static_web_app_name)
API_URL=$(terraform -chdir="$TF" output -raw api_url)
RG=$(grep -E '^resource_group_name' "$TF/terraform.tfvars" | cut -d'"' -f2)
TAG=$(git rev-parse --short HEAD)

# Platform: build in ACR (no local Docker needed), then roll the Container App.
az acr build --registry "$ACR" --image "api:$TAG" "<tool>-platform"
az containerapp update --name "$APP" --resource-group "$RG" \
  --image "$ACR.azurecr.io/api:$TAG" --set-env-vars "APP_VERSION=$TAG"

# App: build against the deployed API, then upload to the Static Web App.
( cd "<tool>-app" && npm ci && VITE_API_BASE="$API_URL" npm run build )
TOKEN=$(az staticwebapp secrets list --name "$SWA" --resource-group "$RG" --query properties.apiKey -o tsv)
npx --yes @azure/static-web-apps-cli deploy "<tool>-app/dist" --deployment-token "$TOKEN" --env production

echo "API: $API_URL"
echo "App: $(terraform -chdir="$TF" output -raw frontend_url)"
```

- **The SWA deployment token** is fetched at run time and never stored.
- **`az acr build`** builds the image in Azure, so the person deploying needs neither Docker nor AcrPush. The build runs as their activated Contributor role.

---

## C.5 README, CI and hand-over

- **README (§8), Deploy section.** Replace the pointer to `terraform/README.md` with three steps:
  1. Activate the PIM group (name from `POC_ENVIRONMENT.md`).
  2. The first time: `terraform -chdir=<tool>-platform/terraform init && terraform -chdir=<tool>-platform/terraform apply`.
  3. Each code change: `./deploy.sh`.
  
  Also give the end date, and point to `POC_ENVIRONMENT.md` for the details.
- **CI:** unchanged. `ci.yml` builds and tests on PR and on push to `main`. CD from GitHub Actions (OIDC) isn't part of v0 of the PoC framework. Don't wire it up, and don't leave a `deploy.yml` stub.
- **Verify (Step 8):** also run `terraform -chdir=<tool>-platform/terraform fmt -check` and `terraform -chdir=<tool>-platform/terraform init -backend=false && terraform -chdir=<tool>-platform/terraform validate`. **Don't run `apply` or `deploy.sh`.** Deploying is the user's step, after PIM activation.
- **Hand-over (Step 10):** what is deployable now (Terraform and `deploy.sh`), what the user does first (activate PIM, `init`/`apply`, `deploy.sh`), and what is deliberately left out (a database in Azure if relevant, CD, a custom domain).
