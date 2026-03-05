---
name: gitflow-release-prepare
version: 1.1.0
description: Analyse unreleased commits and propose a semantic version bump for an Enterspeed project. Use when the user says "prepare a release", "what should the next version be", "check what's unreleased", or "propose a version bump". Run this before gitflow-release-start to review the proposed version before any changes are made.
---

# Git Flow Release — Prepare

Reads the current version from `azure-pipeline.yaml`, pulls the latest branches, analyses unreleased commits, and proposes a semantic version bump. No files are modified and no branches are created — this is a read-only step to let you review and confirm the version before starting the release.

---

## Prerequisites

Run the **gitflow-prerequisites** skill first. If any check fails, stop — do not continue.

---

## Step 1 — Find pipeline file and read current version

Find `azure-pipeline.yaml` (or `azure-pipelines.yaml`):

```bash
ls azure-pipeline.yaml 2>/dev/null || ls azure-pipelines.yaml 2>/dev/null
```

Store the found filename as `PIPELINE_FILE`. If neither file is found, ask the user for the path. Verify the user-provided path exists before continuing.

Extract the three version variables:

```bash
grep -E '^\s*(majorVersion|minorVersion|patchVersion):' "$PIPELINE_FILE"
```

Verify all three keys were found. If any are missing, stop and tell the user:

> "Could not find `majorVersion`, `minorVersion`, or `patchVersion` in `$PIPELINE_FILE`. Check that the file follows the expected format."

If the keys are present but have unexpected formatting (e.g., quoted values, unusual indentation, or YAML nesting), ask the user:

> "Found version keys in `$PIPELINE_FILE` but they may have unexpected formatting. Please verify the exact format matches the standard pattern (e.g., `majorVersion: 1` with no quotes)."

Parse the current version as `{major}.{minor}.{patch}`.

---

## Step 2 — Pull latest branches

```bash
git checkout master && git pull origin master
git checkout develop && git pull origin develop
```

If either command fails, stop and report the error.

---

## Step 3 — Analyse unreleased commits

Find the most recent tag:

```bash
git describe --tags --abbrev=0 2>/dev/null || echo "no-tags"
```

Enterspeed projects use plain semver tags without a `v` prefix (e.g. `1.53.0`, not `v1.53.0`). If the detected tag starts with `v`, stop and tell the user:

> "The most recent tag (`<tag>`) uses a `v` prefix, which doesn't match the expected convention. If you believe your tags follow a different convention, contact your team lead before releasing."

List real commits (excluding merges) since the last tag:

```bash
git log <last-tag>..HEAD --no-merges --oneline
```

If this command fails, stop and report the error:

> "Failed to retrieve commit history. Check your network connection and ensure the repository is accessible."

If no tags exist, list the most recent commits:

```bash
git log --no-merges --oneline -20
```

Before proposing a bump, always run a full log to search commit bodies for `BREAKING CHANGE` (the oneline format above only shows commit subjects):

```bash
git log <last-tag>..HEAD --no-merges --format="%B"
```

If this command fails, stop and report the error.

If a tag exists but no commits are found since it, check if develop and master are on the same commit:

```bash
git rev-parse develop
git rev-parse master
```

If they match, tell the user:

> "No commits found since the last release (`<last-tag>`), and develop and master are on the same commit. There may be nothing to release. Should I still propose a patch bump (`{major}.{minor}.{patch+1}`), or skip the release?"

If they don't match, tell the user:

> "No commits found since the last release (`<last-tag>`) on develop. There may be nothing to release. Should I still propose a patch bump (`{major}.{minor}.{patch+1}`), or skip the release?"

Stop and wait for their answer. If no response is received within a reasonable time (e.g., 5 minutes of inactivity), stop and tell the user:

> "No response received. Please re-run this skill when you're ready to continue."

---

## Step 4 — Propose version bump

Determine the bump type following [Conventional Commits](https://www.conventionalcommits.org/):

- Subject contains `!` (e.g. `feat!:`, `fix!:`) OR any commit body/footer contains `BREAKING CHANGE:` → **major**
- Subject starts with `feat:` or `feat(` → **minor**
- All other commits → **patch**

Apply the highest-priority bump found:

- **major**: `{major+1}.0.0`
- **minor**: `{major}.{minor+1}.0`
- **patch**: `{major}.{minor}.{patch+1}`

Present the full picture to the user:

```
Current version: 1.52.2 (from azure-pipeline.yaml)
Last release tag: 1.52.2

Unreleased commits:
  abc1234 feat: add new dashboard widget
  def5678 fix: correct API timeout handling
  ghi9012 chore: update dependencies

Proposed bump: minor → 1.53.0
```

Ask: "Should I proceed with version `1.53.0`, or would you like a different version? (Must be `MAJOR.MINOR.PATCH`)"

Validate any user-provided version:

1. Format must match `N.N.N` pattern (three numeric parts separated by dots)
2. Version must represent a valid semantic bump from the current version:
   - Cannot be lower than current version
   - Cannot skip versions (e.g., can't go from 1.52.2 to 1.55.0 without explanation)

If the format is invalid or the bump logic seems wrong, reject it and re-prompt:

> "Version `X.Y.Z` doesn't look right. It should be higher than `{current}` and follow semantic versioning. Please provide `MAJOR.MINOR.PATCH` (e.g., 1.53.0)."

If no response is received within a reasonable time, stop and tell the user:

> "No response received. Please re-run this skill when you're ready to continue."

Once confirmed, tell the user:

> "Version `1.53.0` confirmed. When you're ready, I can run **gitflow-release-start** with version `1.53.0` to create the release branch and update the pipeline file. Would you like to proceed now?"

Wait for explicit user confirmation before invoking gitflow-release-start. Do not automatically trigger the next skill.
