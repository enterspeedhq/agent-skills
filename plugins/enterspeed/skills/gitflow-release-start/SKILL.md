---
name: gitflow-release-start
version: 1.1.0
description: Start a git flow release for an Enterspeed project: creates the release branch, updates the pipeline version, and opens PRs to master and develop. Use when the user says "start the release", "create the release branch", or provides a confirmed version (e.g. "start release 1.53.0"). Run gitflow-release-prepare first to determine the version. Follow up with gitflow-release-finish once both PRs are merged.
---

# Git Flow Release — Start

Creates the release branch, updates `azure-pipeline.yaml` with the confirmed version, and opens PRs to master and develop. Run **gitflow-release-prepare** first to determine the version. Once both PRs are merged, run **gitflow-release-finish** to clean up locally and push the tag.

> **Stop on any error** — if any step fails unexpectedly, report the full error output to the user and do not proceed to the next step.

---

## Input

Ask the user for the confirmed version to release (e.g. `1.53.0`). Validate it matches the pattern `N.N.N` before continuing. Use this as `<version>` for all subsequent steps.

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

Verify the GitHub CLI is installed:

```bash
gh --version
```

If not installed, stop and tell the user:
> "GitHub CLI (`gh`) is not installed. Install it with `brew install gh` and authenticate with `gh auth login` first."

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

---

## Step 1 — Find pipeline file

Find `azure-pipeline.yaml` (or `azure-pipelines.yaml`):

```bash
ls azure-pipeline.yaml 2>/dev/null || ls azure-pipelines.yaml 2>/dev/null
```

Store the found filename as `PIPELINE_FILE` and use it consistently in all subsequent steps. If neither file is found, ask the user for the path.

---

## Step 2 — Pull latest branches

```bash
git checkout master && git pull origin master
git checkout develop && git pull origin develop
```

If either command fails, stop and report the error. Do not continue until the user resolves it.

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

Split `<version>` into components using shell commands, then run the update script:

```bash
MAJOR=$(echo "<version>" | cut -d. -f1)
MINOR=$(echo "<version>" | cut -d. -f2)
PATCH=$(echo "<version>" | cut -d. -f3)
MAJOR="$MAJOR" MINOR="$MINOR" PATCH="$PATCH" PIPELINE_FILE="$PIPELINE_FILE" python3 -c "
import re, os
major = os.environ['MAJOR']
minor = os.environ['MINOR']
patch = os.environ['PATCH']
pipeline_file = os.environ['PIPELINE_FILE']
content = open(pipeline_file).read()
content = re.sub(r'^(\s*majorVersion:\s*)\d+', r'\g<1>' + major, content, flags=re.MULTILINE)
content = re.sub(r'^(\s*minorVersion:\s*)\d+', r'\g<1>' + minor, content, flags=re.MULTILINE)
content = re.sub(r'^(\s*patchVersion:\s*)\d+', r'\g<1>' + patch, content, flags=re.MULTILINE)
open(pipeline_file, 'w').write(content)
print(f'Updated {pipeline_file} to {major}.{minor}.{patch}')
"
```

Substitute the actual version string for `<version>` before running. Verify the result:

```bash
grep -E '^\s*(majorVersion|minorVersion|patchVersion):' "$PIPELINE_FILE"
```

If the values are wrong, stop and report the discrepancy. Otherwise commit:

```bash
git add "$PIPELINE_FILE"
git commit -m "Bump version to <version>"
```

---

## Step 5 — Push release branch and open PRs

Push the release branch:

```bash
git push origin release/<version>
```

Open two pull requests. Capture the URL with `--json url --jq '.url'`, then fetch the PR number using `gh pr view` to avoid fragile URL parsing. Substitute the actual version string for `<version>` before running.

**PR 1 — release → master** (the production merge):
```bash
MASTER_PR_URL=$(gh pr create \
  --base master \
  --head "release/<version>" \
  --title "Release <version>" \
  --body "## Release <version>

Bumps version to \`<version>\` in \`$PIPELINE_FILE\`.

### Checklist
- [ ] Version variables updated correctly in \`$PIPELINE_FILE\`
- [ ] CI passes on the release branch
- [ ] Reviewed and approved" \
  --json url --jq '.url')
MASTER_PR_NUMBER=$(gh pr view "$MASTER_PR_URL" --json number --jq '.number')
echo "Master PR: $MASTER_PR_URL (#$MASTER_PR_NUMBER)"
```

**PR 2 — release → develop** (the back-merge):
```bash
DEVELOP_PR_URL=$(gh pr create \
  --base develop \
  --head "release/<version>" \
  --title "Back-merge release <version> into develop" \
  --body "Merges release branch back into develop after the <version> release." \
  --json url --jq '.url')
DEVELOP_PR_NUMBER=$(gh pr view "$DEVELOP_PR_URL" --json number --jq '.number')
echo "Develop PR: $DEVELOP_PR_URL (#$DEVELOP_PR_NUMBER)"
```

If either command fails, stop and report the error.

Show the user both URLs, then say:
> "Two PRs are open:
> - **Master PR**: `$MASTER_PR_URL` (#`$MASTER_PR_NUMBER`)
> - **Develop PR**: `$DEVELOP_PR_URL` (#`$DEVELOP_PR_NUMBER`)
>
> Merge the **master PR first**, then the **develop PR**.
>
> Once both are merged, run the **gitflow-release-finish** skill and provide these PR numbers:
> - Master PR: `$MASTER_PR_NUMBER`
> - Develop PR: `$DEVELOP_PR_NUMBER`"

---

## If something goes wrong

- **Before the PRs are merged**: close both PRs on GitHub, then delete the remote and local release branch:
  ```bash
  git push origin --delete release/<version>
  git branch -D release/<version>
  ```
  The release is fully undone with no impact on master or develop.

- **After master PR merges but before develop PR**: do not skip the back-merge. Merge the develop PR. If it has conflicts, resolve them in the GitHub conflict editor (Edit → resolve conflicts → mark as resolved → commit). If conflicts are too complex for the GitHub editor, check out develop locally, merge master in, resolve, push, then merge the PR.

- **Both PRs have merge conflicts**: resolve the master PR conflict first (it has priority), then handle the develop PR separately.
