---
name: gitflow-release-start
version: 1.2.0
description: Start a git flow release for an Enterspeed project: creates the release branch, updates azure-pipeline.yaml, and commits. Use when the user says "start the release", "create the release branch", or provides a confirmed version (e.g. "start release 1.53.0"). Run gitflow-release-prepare first to determine the version. Follow up with gitflow-release-publish to push and open PRs.
---

# Git Flow Release — Start

Creates the release branch, updates `azure-pipeline.yaml` with the confirmed version, and commits. This skill only makes **local git changes** — no push, no PRs. Run **gitflow-release-prepare** first to determine the version, then **gitflow-release-publish** to push and open PRs.

> **Stop on any error** — if any step fails unexpectedly, report the full error output to the user and do not proceed to the next step.

---

## Input

Ask the user for the confirmed version to release (e.g. `1.53.0`). Validate it matches the pattern `N.N.N` — reject and re-prompt if the format is invalid. Use this as `<version>` for all subsequent steps.

If the user hasn't run **gitflow-release-prepare** yet, suggest they do so first to review the proposed version.

---

## Prerequisites check

Verify git flow is installed:

```bash
git flow version
```

If not installed, stop and tell the user:
> "git flow is not installed. Install it with `brew install git-flow-avh` and run `git flow init` in your project first."

Verify git flow has been initialized:

```bash
git flow config
```

If it fails, stop and tell the user to run `git flow init` first.

Verify git user identity is configured:

```bash
git config user.name && git config user.email
```

If either fails, stop and tell the user:
> "Git user identity is not configured. Set it with `git config user.name 'Your Name'` and `git config user.email 'you@enterspeed.com'`."

Verify the working directory is clean:

```bash
git status --porcelain
```

If there is any output, stop and tell the user:
> "There are uncommitted changes in your working directory. Please commit or stash them before starting a release."

Verify you are not in detached HEAD state:

```bash
git symbolic-ref -q HEAD
```

If this fails, stop and tell the user:
> "You are in detached HEAD state. Check out a branch (e.g. `git checkout develop`) before starting a release."

---

## Step 1 — Find pipeline file

Find `azure-pipeline.yaml` (or `azure-pipelines.yaml`):

```bash
ls azure-pipeline.yaml 2>/dev/null || ls azure-pipelines.yaml 2>/dev/null
```

Store the found filename as `PIPELINE_FILE` and use it consistently in all subsequent steps. If neither file is found, ask the user for the path, then verify it exists and contains all three version keys:

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

If either command fails, stop and report the error.

---

## Step 3 — Start release branch

Check whether the release branch already exists:

```bash
git branch --list "release/<version>"
```

If it returns output, stop and tell the user:
> "A release branch for `<version>` already exists locally. Delete it with `git branch -D release/<version>` if you want to start fresh, or switch to it and continue from Step 4."

Otherwise, start the branch:

```bash
git flow release start <version>
```

This creates and checks out `release/<version>` from `develop`. If it fails, stop and report the error.

---

## Step 4 — Update pipeline file and commit

Copy the update script to a temporary location and run it:

```bash
cp <skill-path>/scripts/update_version.py /tmp/update_version.py
MAJOR=$(echo "<version>" | cut -d. -f1)
MINOR=$(echo "<version>" | cut -d. -f2)
PATCH=$(echo "<version>" | cut -d. -f3)
MAJOR="$MAJOR" MINOR="$MINOR" PATCH="$PATCH" PIPELINE_FILE="$PIPELINE_FILE" python3 /tmp/update_version.py
```

Substitute the actual version string for `<version>` before running. If the script exits with an error, stop and report it.

Verify the result:

```bash
grep -E '^\s*(majorVersion|minorVersion|patchVersion):' "$PIPELINE_FILE"
```

If the values don't match `<version>`, stop and report the discrepancy.

Show the user the updated lines and ask: "The pipeline file has been updated to `<version>`. Ready to commit and proceed to publishing?"

If confirmed, commit:

```bash
git add "$PIPELINE_FILE"
git commit -m "Bump version to <version>"
```

---

## Done

Tell the user:

> "Release branch `release/<version>` is ready with the version commit. Run **gitflow-release-publish** with version `<version>` to push the branch and open PRs."

---

## If something goes wrong

- **Before committing**: delete the local release branch and start over:
  ```bash
  git checkout develop
  git branch -D release/<version>
  ```

- **After committing but before publishing**: the release branch is local only — no impact on master, develop, or GitHub. Delete the branch to abort:
  ```bash
  git checkout develop
  git branch -D release/<version>
  ```
