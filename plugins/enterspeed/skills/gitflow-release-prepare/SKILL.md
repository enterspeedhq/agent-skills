---
name: gitflow-release-prepare
version: 1.0.0
description: Analyse unreleased commits and propose a semantic version bump for an Enterspeed project. Use when the user says "prepare a release", "what should the next version be", "check what's unreleased", or "propose a version bump". Run this before gitflow-release-start to review the proposed version before any changes are made.
---

# Git Flow Release — Prepare

Reads the current version from `azure-pipeline.yaml`, pulls the latest branches, analyses unreleased commits, and proposes a semantic version bump. No files are modified and no branches are created — this is a read-only step to let you review and confirm the version before starting the release.

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

Verify the working directory is clean:

```bash
git status --porcelain
```

If there is any output, stop and tell the user:
> "There are uncommitted changes in your working directory. Please commit or stash them before preparing a release."

Verify you are not in detached HEAD state:

```bash
git symbolic-ref -q HEAD
```

If this fails, stop and tell the user:
> "You are in detached HEAD state. Check out a branch (e.g. `git checkout develop`) before preparing a release."

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
> "The most recent tag (`<tag>`) uses a `v` prefix, which doesn't match the expected convention. Please check your tags before releasing."

List real commits (excluding merges) since the last tag:

```bash
git log <last-tag>..HEAD --no-merges --oneline
```

If no tags exist, list the most recent commits:

```bash
git log --no-merges --oneline -20
```

If no commits are found since the last tag, tell the user:
> "No commits found since the last release (`<last-tag>`). There may be nothing to release. Should I still propose a patch bump (`{major}.{minor}.{patch+1}`), or skip the release?"
Stop and wait for their answer.

Also run a full log to catch `BREAKING CHANGE` in commit footers:

```bash
git log <last-tag>..HEAD --no-merges --format="%B"
```

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

Validate any user-provided version matches the pattern `N.N.N`. If the format is invalid, reject it and re-prompt.

Once confirmed, tell the user:

> "Version `1.53.0` confirmed. When you're ready to start the release, run the **gitflow-release-start** skill and provide version `1.53.0`."
