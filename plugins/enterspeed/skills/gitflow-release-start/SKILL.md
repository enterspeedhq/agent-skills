---
name: gitflow-release-start
version: 1.4.0
description: Start a git flow release for an Enterspeed project: creates the release branch, updates azure-pipeline.yaml, and commits. Use when the user says "start the release", "create the release branch", or provides a confirmed version (e.g. "start release 1.53.0"). Run gitflow-release-prepare first to determine the version. Follow up with gitflow-release-publish to push and open PRs.
---

# Git Flow Release — Start

Creates the release branch, updates `azure-pipeline.yaml` with the confirmed version, and commits. This skill only makes **local git changes** — no push, no PRs. Run **gitflow-release-prepare** first to determine the version, then **gitflow-release-publish** to push and open PRs.

> **Stop on any error** — if any step fails unexpectedly, report the full error output to the user and do not proceed to the next step.

---

## Input

Ask the user for the confirmed version to release. Format must be `N.N.N` (three numeric parts separated by dots, e.g., `1.53.0`).

Validate the format before proceeding:

```bash
if ! [[ "<version>" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Invalid version format. Must be N.N.N (e.g., 1.53.0 is valid, v1.53.0 or 1.53 are invalid)"
  exit 1
fi
```

Reject and re-prompt if the format is invalid. Use this as `<version>` for all subsequent steps.

If the user hasn't run **gitflow-release-prepare** yet, suggest they do so first to review the proposed version.

---

## Prerequisites

Run the **gitflow-prerequisites** skill first. If any check fails, stop — do not continue.

**Required:**
- Python 3.8+ (for the `update_version.py` script)

---

## Step 1 — Find pipeline file

Find the pipeline file (checks both `.yaml` and `.yml` extensions):

```bash
PIPELINE_FILE=$(ls azure-pipelines.yaml 2>/dev/null || ls azure-pipelines.yml 2>/dev/null || ls azure-pipeline.yaml 2>/dev/null || ls azure-pipeline.yml 2>/dev/null)
```

Store the found filename as `PIPELINE_FILE` and use it consistently in all subsequent steps. If none of the four variants are found, stop and tell the user:

> "No pipeline file found (`azure-pipelines.yaml`, `azure-pipelines.yml`, `azure-pipeline.yaml`, or `azure-pipeline.yml`). Make sure you are in the project root directory."

Verify the file contains all three version keys:

```bash
grep -E '^\s*(majorVersion|minorVersion|patchVersion):' "$PIPELINE_FILE"
```

If any of the three keys are missing, stop and tell the user:

> "Could not find `majorVersion`, `minorVersion`, or `patchVersion` in `$PIPELINE_FILE`. Check that the file follows the expected format."

---

## Step 2 — Pull latest branches

```bash
git checkout master && git pull origin master
git checkout develop && git pull origin develop
```

If either pull fails, stop and report the full error. Common causes:

- **Merge conflict**: resolve it on the affected branch before continuing
- **Authentication error**: verify git credentials (`git config --list | grep credential`)

---

## Step 3 — Start release branch

Check whether the release branch already exists locally:

```bash
git branch --list "release/<version>"
```

> **Note**: This checks only local branches. Remote release branches (if they exist from a previous attempt) won't block this step. The push in gitflow-release-publish will detect any remote conflicts.

If it returns output, stop and tell the user:

> "A release branch for `<version>` already exists locally. Delete it with `git branch -D release/<version>` if you want to start fresh, or switch to it and continue from Step 4."

Otherwise, start the branch:

```bash
git flow release start <version>
```

This creates and checks out `release/<version>` from `develop`. If it fails, stop and report the error.

---

## Step 4 — Update pipeline file and commit

> **Note**: This step uses an external Python script (`update_version.py`) to separate file manipulation logic from skill instructions. This keeps the skill focused on orchestration while the script handles YAML parsing. The Enterspeed plugin installer places the script at the path shown below.

Locate the update script:

```
.claude-plugin/plugins/enterspeed/skills/gitflow-release-start/scripts/update_version.py
```

Verify the script exists:

```bash
test -f .claude-plugin/plugins/enterspeed/skills/gitflow-release-start/scripts/update_version.py && echo "Script found" || echo "ERROR: Script not found"
```

If the script is not found, stop and tell the user:

> "The `update_version.py` script could not be found. This skill requires the script at `.claude-plugin/plugins/enterspeed/skills/gitflow-release-start/scripts/update_version.py`. Check that the Enterspeed plugin is properly installed."

Extract the version components and run the update script (replacing `<version>` with the actual version string, e.g., if the user said "1.53.0", use that value):

```bash
MAJOR=$(echo "<version>" | cut -d. -f1)
MINOR=$(echo "<version>" | cut -d. -f2)
PATCH=$(echo "<version>" | cut -d. -f3)
MAJOR="$MAJOR" MINOR="$MINOR" PATCH="$PATCH" PIPELINE_FILE="$PIPELINE_FILE" python3 .claude-plugin/plugins/enterspeed/skills/gitflow-release-start/scripts/update_version.py
```

If the script exits with an error, stop and report it. Then show the current file contents for debugging:

```bash
cat "$PIPELINE_FILE" | head -20
```

Verify the updated values match the expected version:

```bash
grep -E "^\s*majorVersion:\s*$MAJOR" "$PIPELINE_FILE"
grep -E "^\s*minorVersion:\s*$MINOR" "$PIPELINE_FILE"
grep -E "^\s*patchVersion:\s*$PATCH" "$PIPELINE_FILE"
```

Each grep should return exactly one line. If any grep returns nothing, stop and tell the user:

> "Version update failed. Expected `<version>` but the values in `$PIPELINE_FILE` don't match. The file may have unexpected formatting or the version keys are missing."

Then show the relevant section of the file for debugging:

```bash
grep -B2 -A2 -E '^\s*(majorVersion|minorVersion|patchVersion):' "$PIPELINE_FILE"
```

Show the user the updated lines and ask: "The pipeline file has been updated to `<version>`. Ready to commit? (Note: This only commits locally—publishing happens in the next skill.)"

If the user confirms, commit:

```bash
git add "$PIPELINE_FILE"
git commit -m "Bump version to <version>"
```

If the user declines:

- The release branch exists but has no commits yet
- The pipeline file changes are uncommitted (you can see them with `git diff`)
- Options:
  1. If they want to adjust the version, revert the file changes (`git checkout "$PIPELINE_FILE"`) and re-run this skill with a different version
  2. If they want to abort completely, follow the "Before committing (Step 4)" cleanup instructions below

---

## Done

Tell the user:

> "Release branch `release/<version>` is ready with the version commit. Run **gitflow-release-publish** with version `<version>` to push the branch and open PRs."

---

## If something goes wrong

- **Before committing** (if the user declines in Step 4 or the script fails): Delete the local release branch and start over:

  ```bash
  git checkout develop
  git branch -D release/<version>
  ```

  This removes the release branch cleanly. Any uncommitted file changes will remain; reset them with `git checkout <file>` if needed.

- **After committing but before publishing (between Step 4 and gitflow-release-publish)**: The release branch with its commit exists **locally only** — no changes have been pushed to GitHub, so there's no impact on master, develop, or remote branches. At this point:
  - **Current state**: You have a local `release/<version>` branch with the version commit
  - **No remote impact**: Nothing has been pushed yet

  You have two options:
  1. **Continue with publishing**: If the commit is correct, proceed with **gitflow-release-publish**.
  2. **Abort and clean up**: Delete the release branch to discard all changes:
     ```bash
     git checkout develop
     git branch -D release/<version>
     ```
     This is safe because nothing has been pushed yet. You can re-run this skill to start fresh.

- **After starting gitflow-release-publish**: If you've started **gitflow-release-publish** but it failed mid-way, see the rollback instructions in that skill for proper cleanup.
