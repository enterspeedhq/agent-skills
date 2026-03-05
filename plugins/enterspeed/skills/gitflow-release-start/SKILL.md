---
name: gitflow-release-start
version: 1.0.0
description: Start a git flow release for an Enterspeed project: reads version from azure-pipeline.yaml, proposes a semantic bump from git log, creates the release branch, updates the pipeline version, and opens PRs to master and develop. Use when the user says "release", "cut a release", "start a release", "git flow release", or "bump the version". Follow up with the gitflow-release-finish skill once both PRs are merged.
---

# Git Flow Release — Start

Handles the first half of the git flow release process: proposes a version bump, creates the release branch, updates `azure-pipeline.yaml`, and opens PRs to master and develop. Once both PRs are merged, run the **gitflow-release-finish** skill to clean up locally and push the tag.

> **Stop on any error** — if any step fails unexpectedly, report the full error output to the user and do not proceed to the next step.

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

## Step 1 — Find pipeline file and read current version

Find `azure-pipeline.yaml` (or `azure-pipelines.yaml`):

```bash
ls azure-pipeline.yaml 2>/dev/null || ls azure-pipelines.yaml 2>/dev/null
```

Store the found filename as `PIPELINE_FILE` and use it consistently in all subsequent steps. If neither file is found, ask the user for the path.

Extract the three version variables from `$PIPELINE_FILE`:

```bash
grep -E '^\s*(majorVersion|minorVersion|patchVersion):' "$PIPELINE_FILE"
```

Parse `majorVersion`, `minorVersion`, and `patchVersion`. The current version is `{major}.{minor}.{patch}`.

---

## Step 2 — Pull latest and propose version bump

Pull the latest changes from both branches before inspecting commits:

```bash
git checkout master && git pull origin master
git checkout develop && git pull origin develop
```

If either command fails, stop and report the error. Do not continue until the user resolves it.

Find the most recent tag:

```bash
git describe --tags --abbrev=0 2>/dev/null || echo "no-tags"
```

Enterspeed projects use plain semver tags without a `v` prefix (e.g. `1.53.0`, not `v1.53.0`). If the detected tag starts with `v`, stop and tell the user:
> "The most recent tag (`<tag>`) uses a `v` prefix, which doesn't match the expected convention. Please check your tags and correct the format before releasing."

List real commits (excluding merges) since the last tag:

```bash
git log <last-tag>..HEAD --no-merges --oneline
```

If no tags exist, list the most recent commits:

```bash
git log --no-merges --oneline -20
```

If no commits are found since the last tag, tell the user:
> "No commits found since the last release. There may be nothing to release. Should I still proceed with a patch bump (`{major}.{minor}.{patch+1}`), or skip the release?"
Stop and wait for their answer before continuing.

Determine the suggested bump following [Conventional Commits](https://www.conventionalcommits.org/). Check commit subjects (the `--oneline` output) and also run a full log to catch `BREAKING CHANGE` in commit footers:

```bash
git log <last-tag>..HEAD --no-merges --format="%B"
```

Bump rules (highest priority wins):

- Subject contains `!` (e.g. `feat!:`, `fix!:`) OR any commit body/footer contains `BREAKING CHANGE:` → **major** bump
- Subject starts with `feat:` or `feat(` → **minor** bump
- All other commits → **patch** bump

Apply the highest-priority bump found:

- **major**: `{major+1}.0.0`
- **minor**: `{major}.{minor+1}.0`
- **patch**: `{major}.{minor}.{patch+1}`

Present the commits and proposed version:

```
Current version: 1.52.2
Unreleased commits:
  abc1234 feat: add new dashboard widget
  def5678 fix: correct API timeout handling
  ghi9012 chore: update dependencies

Proposed bump: minor → 1.53.0
```

Ask: "Should I proceed with version `1.53.0`, or would you like a different version? (Must be semver format: `MAJOR.MINOR.PATCH`)"

Validate any user-provided version matches the pattern `N.N.N` before continuing. Use the confirmed version as `<version>` for all subsequent steps.

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

Split `<version>` into components and export them as shell variables, then run the update script — no manual placeholder replacement needed:

```bash
MAJOR=<major> MINOR=<minor> PATCH=<patch> PIPELINE_FILE="$PIPELINE_FILE" python3 -c "
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

Substitute the actual numeric values of `<major>`, `<minor>`, `<patch>` before running. Verify the result:

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

Open two pull requests. Use `--json url --jq '.url'` to reliably capture the PR URL. Substitute the actual version string for `<version>` before running.

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
MASTER_PR_NUMBER=$(basename "$MASTER_PR_URL")
echo "Master PR: $MASTER_PR_URL"
```

**PR 2 — release → develop** (the back-merge):
```bash
DEVELOP_PR_URL=$(gh pr create \
  --base develop \
  --head "release/<version>" \
  --title "Back-merge release <version> into develop" \
  --body "Merges release branch back into develop after the <version> release." \
  --json url --jq '.url')
DEVELOP_PR_NUMBER=$(basename "$DEVELOP_PR_URL")
echo "Develop PR: $DEVELOP_PR_URL"
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

- **After master PR merges but before develop PR**: do not skip the back-merge. Merge the develop PR (resolving any conflicts in GitHub if needed) — develop must stay in sync with master.
