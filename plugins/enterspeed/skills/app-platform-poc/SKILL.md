---
name: app-platform-poc
description: Build a PoC or internal tool from an idea plus requirements, following the Enterspeed app + platform blueprint (React app + .NET platform, optional Postgres, optional auth). Use when the user says "build a PoC", "build a proof of concept", "scaffold a new internal tool", "build this idea as app + platform", "follow the app platform blueprint", or describes a tool idea and asks you to implement it from scratch. Also use when adding features to a tool that was already scaffolded this way. Do not use for changes to existing production repos that don't follow the blueprint.
---

# App + Platform PoC Builder

You are the engineer who takes an idea and a set of requirements and turns it into a working proof of concept: a React frontend (`<tool>-app`) and a .NET backend (`<tool>-platform`) that run locally, build clean, have tests, a README, and an infra skeleton for hand-over.

The technical decisions are already made for you — they live in the team blueprint referenced below. Your job is to understand the idea, plan against the blueprint, and implement it. Don't redesign the stack.

---

## Step 1: Read the core blueprint

Read `<skill-path>/references/app-platform-blueprint.md` **in full before writing any code**. It is the source of truth for the stack, repository layout, file contents, and conventions, and it contains the code you should use verbatim (with the `AppTemplate` / `app-template` placeholders replaced).

Two optional appendices sit beside it. **Don't read them yet** — they only apply if the plan calls for them, and Step 7 tells you when:

| File | Applies when |
|---|---|
| `references/appendix-b-database.md` | the tool persists data — or has auth |
| `references/appendix-a-auth.md` | the tool needs a login and/or admin area |

The blueprint is a verbatim copy of the team document — treat it as spec, not suggestion. Where it conflicts with your own preferences, the blueprint wins. Where it is silent, use judgement and say so.

If the core file can't be read, **stop** — the skill is installed incorrectly and nothing below will work. Say which path you tried, and give the remedy: `claude plugin update enterspeed@enterspeed`, or if they're working on the skill itself, check that the branch adding it is the one checked out. Resume at Step 1 once they confirm.

---

## Step 2: Collect the idea and the requirements

The input may arrive as a single sentence, a bullet list of requirements, a linked or pasted document, or a Shortcut story. Read any file, doc, or story that is referenced before asking anything — don't ask for information you can go and read.

If something referenced **can't** be read — a private Shortcut story, a dead link, a path that isn't there — don't guess at its contents and don't stop. Say which one failed and why, ask the user to paste the relevant part, and if they'd rather push on, continue from what's in the prompt and record the gap as an explicit assumption in Step 3.

From the input, work out the decisions in blueprint §3:

1. **Tool name** — kebab and Pascal tokens (§2).
2. **Persistence** — does it store data? If it only transforms, validates, or proxies, there is no database.
3. **Auth** — does it need a login and/or admin area? Auth requires the database.
4. **Features** — each becomes one controller (+ service if there's logic) and one frontend page. Watch for the "upload → preview → ingest" shape.
5. **Domain entities** — only if persisting.
6. **External integrations** — each becomes a typed `HttpClient`.
7. **Admin-managed config** — a settings entity + screen (needs database + auth).

Infer what you reasonably can and record it as an assumption. Ask only about the things that materially change what gets built and that you cannot infer — typically the tool name, the target folder, and the database/auth decisions. Ask them in **one grouped round**, not a drip of questions.

If the requirements imply org-wide SSO / Entra ID, say plainly that it is out of scope for this blueprint (Appendix A is seeded username/password) and either proceed with the simple approach or stop for a decision — the user's call.

---

## Step 3: Present the plan and wait for a go-ahead

Present a short plan before touching the filesystem:

- **Tool name** — kebab / Pascal tokens, and the folder names that follow from them.
- **Target path** — the absolute path the two solutions will be created under.
- **Database** — yes/no, and why. **Auth** — yes/no, and why.
- **Features** — a table: feature → endpoints → frontend page.
- **Entities** — if persisting. **Integrations** — if any.
- **Out of scope** — what you are deliberately not building.
- **Assumptions** — one line each.

**Stop and wait for confirmation.** Do not scaffold anything before the user confirms. If they correct something, revise the plan and present it again.

---

## Step 4: Check prerequisites

Run the blueprint's one-liner (`dotnet --list-sdks; node -v; npm -v; docker --version`), plus `docker info` if you'll use compose, plus `dotnet ef --version` only if the tool has a database.

- **.NET SDK or Node missing, or below the versions the blueprint states** → **stop and ask them to install it.** Nothing gets built without these, so there's no fallback to offer — but make the stop useful: name the tool and the version you found, give the `winget` / Homebrew command from the blueprint, and say you'll pick up at Step 5 once they confirm it's installed. Don't re-run Steps 1–3; the plan is already agreed.
- **Docker unavailable — missing, or the daemon isn't running — and the tool is stateless** → note it, tell the user they'll run `dotnet run` + `npm run dev` instead of compose, and continue.
- **Docker unavailable and the tool has a database** → don't just stop. Say what's unavailable, then offer the two ways forward and let the user choose: point `ConnectionStrings__DefaultConnection` at any reachable Postgres (a native install, an existing container, a shared dev server) and skip the compose run, or pause until Docker is up. The compose file gets written either way — only the local smoke test changes.
- **dotnet-ef missing and the tool has a database** → install it with the command from Appendix B, then continue.

---

## Step 5: Confirm the target location

Resolve the absolute path for the new `<tool>/` folder and check it before writing:

- Path doesn't exist → create it and continue.
- Path exists and is empty → continue.
- Path already contains `<tool>-app` and `<tool>-platform` → this is an existing blueprint solution. Go to **Step 6**.
- Path exists with other content → **stop** and ask where to put it. Never overwrite or delete existing files to make room.

---

## Step 6: Extending an existing blueprint solution

Only when Step 5 found an existing `<tool>-app` + `<tool>-platform` pair. Same job, shorter path — you're adding to a solution that already follows the blueprint, so scaffolding, Docker, terraform, and CI are already done.

1. Read the existing shape first: the controllers, the api modules, `ServiceCollectionExtensions`, and whether the solution has a database and auth. What's already there beats what the blueprint's defaults would be.
2. Skip Step 7's scaffolding and hand-over furniture — the **platform baseline**, the **Dockerfile / `.dockerignore` / compose** set, the **terraform skeleton**, and the **CI workflow** already exist. Do only the **features**, their **frontend** pages and api modules, their **tests**, and whatever the **README** needs for the new work.
3. If the existing solution **deviates from the blueprint** — different folder layout, entities returned from controllers, no DTO mirror — say so and ask whether to match the existing pattern or bring it in line. **Don't silently reshape working code** to match the blueprint; that's a decision for the user, and it's outside what "add this feature" asked for.
4. If the tool needs a database or auth it doesn't have yet, apply the relevant appendix as in Step 7, and say plainly that this is a structural change to an existing tool, not just a feature.

Then continue at Step 8 (verify).

---

## Step 7: Build, in this order

1. **Platform baseline** — scaffold, `Program.cs`, `ServiceCollectionExtensions.cs`, appsettings (blueprint §6.1–6.4). Delete the template's `WeatherForecast` files.
2. **Database** — only if the tool persists data (or has auth). Read `references/appendix-b-database.md` now, then apply it.
3. **Auth** — only if the tool needs a login/admin area, and only after Appendix B. Read `references/appendix-a-auth.md` now, then apply it. Create the EF migration once *all* entities exist, including `Users` — one `InitialCreate`, not a pair (B.7).
4. **Features** — controllers, services, entities (§6.5). For every endpoint, write the C# DTO **and** its mirrored TypeScript interface in the same change set (§4). Controllers return DTOs, never EF entities.
5. **Dockerfile, `.dockerignore`, `docker-compose.yml`** (§6.7). The `.dockerignore` is required, not optional.
6. **Frontend** — scaffold, config, api client, shell, then one page + one typed api module per feature (§7). Use the Appendix A auth shell instead of the plain shell if the tool has auth.
7. **Tests** — both test projects, wired up during scaffolding, not after (Testing section). Unit-test the real logic — parsers, transforms, validators — and use golden-file tests where output must match an external contract.
8. **README** at the top level (§8) — a new developer must be able to run the tool from it alone, including the full env var table.
9. **Terraform skeleton** — the three files in §10. A components manifest and stubs, **not** apply-ready Terraform.
10. **CI workflow** and `.gitignore` (CI/CD section, §11).

While building:

- Replace `AppTemplate` / `app-template` with the real tokens everywhere, including namespaces, DB name, and JWT issuer/audience.
- Copy the **Appendix A security wiring verbatim** — BCrypt, JWT signing, the httpOnly `SameSite=Strict` cookie, token validation. Vary only the things the appendix says may vary (roles, seeded users, `create-user`, token lifetime).
- Stay lean. No OpenTelemetry, rate limiting, queues, or extra libraries unless a requirement genuinely needs one — and if you add one, say why in the hand-over.
- Never commit secrets. Dev-only placeholder keys go in `appsettings.Development.json` / compose exactly as the blueprint shows; real values come from env vars or Key Vault.
- Never commit fixtures containing personal or customer data. Gitignore them and use synthetic samples.

---

## Step 8: Verify — actually run it

Run, from the real project paths:

```bash
dotnet build          # platform
dotnet test           # platform
npm run build         # app
npm test              # app
```

Then a local smoke test: bring the API up (`docker compose up --build`, or `dotnet run` for a stateless tool), start the frontend, exercise the main flow, and log in if the tool has auth.

Finally, the dependency check from §11: `dotnet list package --vulnerable --include-transitive` and `npm audit`.

If something fails, fix it and re-run. If the failure comes from the blueprint's own instructions, fix it in the generated code and flag the discrepancy in the hand-over so the blueprint can be corrected. **Never report success on a command you didn't run or that didn't pass** — quote the actual output instead.

---

## Step 9: Walk the conventions checklist

Go through the §11 checklist item by item and report each as pass, fixed, or not applicable. Don't just assert it's done — check.

---

## Step 10: Hand over

Close with a short hand-over:

- What was built — the two solutions, the features, database and auth decisions.
- How to run it locally — the two commands, plus seeded credentials if auth.
- What is deliberately incomplete — the Terraform skeleton and any CD stub are for the infra owner.
- What the receiver must supply — secrets and env vars, named.
- Known gaps, deferred items, and any deviation you made from the blueprint, with the reason.

For the repository's own documentation — contributing guide, architecture notes, a `CLAUDE.md` — the **repo-scaffold** skill covers that ground; the README in Step 7 is the tool's run-and-env-vars doc, not a substitute for it.

Do not `git init`, commit, or push unless the user asks. If they do ask, show the proposed commit message and wait for confirmation.

---

## Guardrails

- **Never** build this as a Python app, a Streamlit app, or a single fused frontend+backend project. Always the app + platform split.
- Database and auth are **optional** — leaving them out is the default, not a shortcut. Don't add either without a requirement that needs it, and don't read an appendix you don't need.
- Don't author apply-ready Terraform, don't deploy, and don't wire a CD pipeline. Those belong to the infra owner (§10).
- One skill, one job: this builds and extends blueprint-shaped PoCs. It doesn't review PRs, publish stories, or manage releases — use the dedicated skills for those.
