---
name: gitflow-release
version: 1.4.0
description: Automate git flow releases for Enterspeed projects. Use when the user says "release", "cut a release", "start a release", "git flow release", or "bump the version".
---

# Git Flow Release

Automates the full git flow release process: reads the current semantic version from `azure-pipeline.yaml`, proposes a version bump based on unreleased commits, creates a release branch, updates the pipeline version, opens PRs to master and develop, then cleans up locally and tags after both PRs merge.

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

## Step 2 — Propose version bump

Find the most recent tag:

```bash
git describe --tags --abbrev=0 2>/dev/null || echo "no-tags"
```

Tags follow plain semver format without a `v` prefix (e.g. `1.53.0`, not `v1.53.0`).

List real commits (excluding merges) since the last tag:

```bash
git log <last-tag>..HEAD --no-merges --oneline
```

If no tags exist, list the most recent commits:

```bash
git log --no-merges --oneline -20
```

If no commits are found since the last tag, tell the user:
> "No commits found since the last release. There may be nothing to release. Should I still proceed with a patch bump, or skip the release?"
Stop and wait for their answer before continuing.

Determine the suggested bump from commit messages:

- Any message containing `BREAKING CHANGE`, `feat!`, or `fix!` → **major** bump
- Any message starting with `feat:` or `feat(` → **minor** bump
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

## Step 3 — Pull latest master and develop

```bash
git checkout master && git pull origin master
git checkout develop && git pull origin develop
```

If either command fails, stop and report the error. Do not continue until the user resolves it.

---

## Step 4 — Start release branch

```bash
git flow release start <version>
```

This creates and checks out `release/<version>` from `develop`. If it fails, stop and report the error.

---

## Step 5 — Update pipeline file and commit

Split `<version>` into components and export them as shell variables, then run the update script using those variables — no manual placeholder replacement needed:

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

## Step 6 — Push release branch and open PRs

Push the release branch:

```bash
git push origin release/<version>
```

Open two pull requests. Substitute the actual version string for `<version>` in each command before running:

**PR 1 — release → master** (the production merge):
```bash
gh pr create \
  --base master \
  --head "release/<version>" \
  --title "Release <version>" \
  --body "## Release <version>

Bumps version to \`<version>\` in \`$PIPELINE_FILE\`.

### Checklist
- [ ] Version variables updated correctly in \`$PIPELINE_FILE\`
- [ ] CI passes on the release branch
- [ ] Reviewed and approved"
```

**PR 2 — release → develop** (the back-merge):
```bash
gh pr create \
  --base develop \
  --head "release/<version>" \
  --title "Back-merge release <version> into develop" \
  --body "Merges release branch back into develop after the <version> release."
```

Show the user both PR URLs, then say:
> "Two PRs are open:
> - **Master PR**: `<master-pr-url>`
> - **Develop PR**: `<develop-pr-url>`
>
> Merge the **master PR first**, then the **develop PR**. Reply here when both are merged and I'll clean up locally and create the release tag."

Wait for the user to reply that both PRs are merged before continuing.

---

## Step 7 — Local cleanup and tagging

Wait for the user to confirm both PRs are merged. Before proceeding, verify both are actually merged using the PR numbers returned in Step 6:

```bash
gh pr view <master-pr-number> --json state --jq '.state'
gh pr view <develop-pr-number> --json state --jq '.state'
```

Both must return `MERGED`. If either returns `OPEN` or `CLOSED`, tell the user and stop:
> "The PR doesn't appear to be merged yet. Please merge it on GitHub and let me know when done."

Pull the updated branches:

```bash
git checkout master && git pull origin master
git checkout develop && git pull origin develop
```

Delete the local release branch (the remote is deleted by GitHub on merge):

```bash
git branch -d release/<version>
```

Check that the tag does not already exist before creating it:

```bash
git tag -l "<version>"
```

If the tag already exists, tell the user and skip tag creation. Otherwise, tag the current master HEAD and push:

```bash
git tag <version> $(git rev-parse master)
git push origin <version>
```

Show the user a final summary:

```
Release <version> complete:
  - master: updated and tagged <version>
  - develop: back-merged
  - Local release branch: deleted
  - Tag <version>: pushed to origin
```

---

## If something goes wrong

- **Before the PRs are merged**: close both PRs on GitHub, then delete the remote and local release branch:
  ```bash
  git push origin --delete release/<version>
  git branch -D release/<version>
  ```
  The release is fully undone with no impact on master or develop.

- **After master PR merges but before develop PR**: do not skip the back-merge. Merge the develop PR (resolving any conflicts in GitHub if needed) — develop must stay in sync with master.

- **After both PRs merge**: the release is complete. If you need to undo it, a revert commit on master is the safest path. Team coordination is required.
