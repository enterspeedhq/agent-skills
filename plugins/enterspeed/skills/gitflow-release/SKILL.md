---
name: gitflow-release
version: 1.2.0
description: Automate git flow releases for Enterspeed projects. Use when the user says "release", "cut a release", "start a release", "git flow release", or "bump the version". Reads version from azure-pipeline.yaml, proposes a semantic bump from git log, and runs the full git flow release cycle.
---

# Git Flow Release

Automates the full git flow release process: reads the current semantic version from `azure-pipeline.yaml`, proposes a version bump based on unreleased commits, runs the git flow release cycle, updates the pipeline version, and asks to push.

> **Stop on any error** — if any step fails unexpectedly, report the full error output to the user and do not proceed to the next step.

---

## Prerequisites check

Before starting, verify that git flow is installed:

```bash
git flow version
```

If git flow is not installed, stop and tell the user:
> "git flow is not installed. Install it with `brew install git-flow-avh` and run `git flow init` in your project first."

Verify that git flow has been initialized in the repo:

```bash
git flow config
```

If it fails, stop and tell the user to run `git flow init` first.

---

## Step 1 — Read current version

Find `azure-pipeline.yaml` in the current working directory:

```bash
ls azure-pipeline.yaml 2>/dev/null || ls azure-pipelines.yaml 2>/dev/null
```

If not found, ask the user: "I couldn't find azure-pipeline.yaml in the current directory. What is the path to your pipeline file?"

Extract the three version variables:

```bash
grep -E '^\s*(majorVersion|minorVersion|patchVersion):' azure-pipeline.yaml
```

Parse the values of `majorVersion`, `minorVersion`, and `patchVersion` from the output. The current version is `{major}.{minor}.{patch}`.

---

## Step 2 — Propose version bump

Find the most recent semver tag:

```bash
git describe --tags --abbrev=0 2>/dev/null || echo "no-tags"
```

If a tag exists, list real commits (excluding merges) since that tag:

```bash
git log <last-tag>..HEAD --no-merges --oneline
```

If no tags exist, list the most recent commits:

```bash
git log --no-merges --oneline -20
```

Analyze the commit messages and determine the suggested bump:

- Any message containing `BREAKING CHANGE`, `feat!`, or `fix!` → **major** bump
- Any message starting with `feat:` or `feat(` → **minor** bump
- All other commits → **patch** bump

Apply the highest-priority bump found. Calculate the proposed new version:

- **major**: `{major+1}.0.0`
- **minor**: `{major}.{minor+1}.0`
- **patch**: `{major}.{minor}.{patch+1}`

Present the unreleased commits and proposed version to the user:

```
Current version: 1.52.2
Unreleased commits:
  abc1234 feat: add new dashboard widget
  def5678 fix: correct API timeout handling
  ghi9012 chore: update dependencies

Proposed bump: minor → 1.53.0
```

Ask: "Should I proceed with version `1.53.0`, or would you like a different version?"

Wait for the user to confirm or provide an alternative version. Use their answer as `<version>` for all subsequent steps.

---

## Step 3 — Pull latest master and develop

```bash
git checkout master && git pull origin master
git checkout develop && git pull origin develop
```

If either command fails (e.g. uncommitted changes, merge conflicts), stop and report the error. Do not continue until the user resolves it.

---

## Step 4 — Start release branch

```bash
git flow release start <version>
```

This creates and checks out `release/<version>` from `develop`. If it fails, stop and report the error.

---

## Step 5 — Update azure-pipeline.yaml and commit

Split `<version>` into its three components (e.g. `1.53.0` → major=1, minor=53, patch=0).

Update the three variables in `azure-pipeline.yaml` using multiline-aware regex to handle any indentation or spacing:

```bash
python3 -c "
import re
content = open('azure-pipeline.yaml').read()
content = re.sub(r'^(\s*majorVersion:\s*)\d+', r'\g<1><MAJOR>', content, flags=re.MULTILINE)
content = re.sub(r'^(\s*minorVersion:\s*)\d+', r'\g<1><MINOR>', content, flags=re.MULTILINE)
content = re.sub(r'^(\s*patchVersion:\s*)\d+', r'\g<1><PATCH>', content, flags=re.MULTILINE)
open('azure-pipeline.yaml', 'w').write(content)
print('Updated azure-pipeline.yaml to <MAJOR>.<MINOR>.<PATCH>')
"
```

Replace `<MAJOR>`, `<MINOR>`, `<PATCH>` with the actual numeric values before running.

Verify the change looks correct before committing:

```bash
grep -E '^\s*(majorVersion|minorVersion|patchVersion):' azure-pipeline.yaml
```

If the values are not what you expect, stop and report the discrepancy to the user. Otherwise commit:

```bash
git add azure-pipeline.yaml
git commit -m "Bump version to <version>"
```

---

## Step 6 — Push release branch and open PRs

Push the release branch to origin:

```bash
git push origin release/<version>
```

Then open two pull requests using the GitHub CLI:

**PR 1 — release → master** (the production merge):
```bash
gh pr create \
  --base master \
  --head release/<version> \
  --title "Release <version>" \
  --body "## Release <version>

Bumps version to \`<version>\` in \`azure-pipeline.yaml\`.

### Checklist
- [ ] Version variables updated correctly in \`azure-pipeline.yaml\`
- [ ] CI passes on the release branch
- [ ] Reviewed and approved"
```

**PR 2 — release → develop** (the back-merge):
```bash
gh pr create \
  --base develop \
  --head release/<version> \
  --title "Back-merge release <version> into develop" \
  --body "Merges release branch back into develop after the \`<version>\` release."
```

Show the user both PR URLs and tell them:
> "Two PRs are open. Merge the **master PR first**, then the **develop PR**. Come back here once both are merged and I'll clean up locally and create the tag."

---

## Step 7 — Local cleanup and tagging

Wait for the user to confirm both PRs are merged. Then:

Pull the updated branches:

```bash
git checkout master && git pull origin master
git checkout develop && git pull origin develop
```

Delete the local release branch (the remote was deleted by GitHub on merge):

```bash
git branch -d release/<version>
```

Create the version tag on the master merge commit and push it:

```bash
git tag <version> master
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

- **After master PR merges but before develop PR**: merge the develop PR (or resolve conflicts and merge). Do not skip the back-merge — develop must stay in sync with master.

- **After both PRs merge**: the release is complete. If you need to undo it, a revert commit on master is the safest path. Team coordination is required.
