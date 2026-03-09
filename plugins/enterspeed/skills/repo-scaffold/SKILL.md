---
name: repo-scaffold
description: Generate standard repository documentation for a project. Use when the user says "scaffold this repo", "set up repo docs", "create contributing docs", "initialise repo docs", "add a CLAUDE.md", "what docs does this repo need", or "scaffold docs".
---

# Repo Scaffold

Reads the repository, infers what it can, asks only what it can't, then generates the missing documentation files.

---

## Step 1 — Read the repo

Scan the root and `.github/` for:

- Existing docs: `README.md`, `CONTRIBUTING.md`, `DEVELOPMENT.md`, `CLAUDE.md`, `docs/architecture.md`, `.github/PULL_REQUEST_TEMPLATE.md`
- Stack signals: `package.json`, `*.csproj`, `go.mod`, `requirements.txt`, `Makefile`, `docker-compose.yml`, `Dockerfile`
- CI/CD: `.github/workflows/`, `azure-pipeline*.yaml`, `Jenkinsfile`
- Existing top-level folder structure

Note what already exists — do not overwrite it. Only generate what's missing.

---

## Step 2 — Infer what you can

From what you read, determine:

- **Stack** — language, framework, runtime
- **Local setup required?** — yes if `Makefile`, `docker-compose.yml`, scripts, or a non-trivial dependency list exists
- **CI/CD tool** — from workflow files
- **Repo type** — library, service, tooling, content/config

---

## Step 3 — Ask what you can't infer

Ask only these, in a single message:

1. **Audience** — Internal team only, or also external contributors?
2. **Conventions** — Any coding or workflow conventions not enforced by tooling?
3. **Architecture intent** — Any design decision worth capturing that a new developer would otherwise have to reverse-engineer?
4. **Claude guidance** — Anything Claude should always do, or never do, in this repo?

Skip any question the repo type makes irrelevant. Wait for answers before continuing.

---

## Step 4 — Determine which docs to generate

| Doc | Generate if |
|-----|-------------|
| `README.md` | Missing or is a placeholder |
| `CONTRIBUTING.md` | Missing |
| `DEVELOPMENT.md` | Missing AND local setup is non-trivial |
| `CLAUDE.md` | Missing AND user provided Claude guidance or conventions worth capturing |
| `docs/architecture.md` | Missing AND user described an architecture decision worth recording |
| `.github/PULL_REQUEST_TEMPLATE.md` | Missing AND repo has an active PR workflow |

Tell the user which files you'll generate before writing them. If there is nothing to generate, say so and stop.

---

## Step 5 — Generate the files

Write each file. Keep them concise — useful on day one, not exhaustive. Use `TODO:` placeholders where the team needs to fill in specifics.

**README.md** — What it is, how to get started, link to CONTRIBUTING if it exists.

**CONTRIBUTING.md** — How to contribute: branch conventions, PR process, any conventions from Step 3, link to DEVELOPMENT.md if it exists.

**DEVELOPMENT.md** — Prerequisites, install, run, test. Nothing else.

**CLAUDE.md** — Conventions to follow, patterns to avoid, tool preferences — anything from Step 3 that applies to AI-assisted work.

**docs/architecture.md** — The decision from Step 3: what was decided, why, and what it rules out.

**.github/PULL_REQUEST_TEMPLATE.md** — A short checklist of what every PR should include for this repo type.

---

## Step 6 — Close

List the files written. Tell the user:

> "Review each file and fill in the `TODO:` sections before committing."

Do not commit, push, or open a PR.
