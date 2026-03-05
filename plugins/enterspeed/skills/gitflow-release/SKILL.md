---
name: gitflow-release
version: 1.0.0
description: Run a git flow release for an Enterspeed project. Use when the user says "release", "cut a release", "start a release", "git flow release", or "bump the version". Reads the current version from azure-pipeline.yaml, analyses git log since the last tag to propose a major/minor/patch bump, pulls master and develop, runs git flow release start/finish with a version commit, then asks to push.
---

# Git Flow Release

Automates the full git flow release process: reads the current semantic version from `azure-pipeline.yaml`, proposes a version bump based on unreleased commits, runs the git flow release cycle, updates the pipeline version, and asks to push.

---

## Prerequisites check

Before starting, verify that:

```bash
git flow version
```

If git flow is not installed, stop and tell the user:
> "git flow is not installed. Install it with `brew install git-flow-avh` and run `git flow init` in your project first."

Also verify that `git flow` has been initialized in the repo:

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

If a tag exists, list commits since that tag:

```bash
git log <last-tag>..HEAD --oneline
```

If no tags exist, list all commits:

```bash
git log --oneline -20
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

If either pull fails (e.g. uncommitted changes, merge conflicts), stop and report the error to the user.

---

## Step 4 — Start release branch

```bash
git flow release start <version>
```

This creates and checks out `release/<version>` from `develop`.

---

## Step 5 — Update azure-pipeline.yaml and commit

Split `<version>` into its three components (e.g. `1.53.0` → major=1, minor=53, patch=0).

Update the three variables in `azure-pipeline.yaml` using exact line replacements. Use a Python one-liner to make the replacements precisely:

```bash
python3 -c "
import re, sys
content = open('azure-pipeline.yaml').read()
content = re.sub(r'(majorVersion:\s*)\d+', r'\g<1><MAJOR>', content)
content = re.sub(r'(minorVersion:\s*)\d+', r'\g<1><MINOR>', content)
content = re.sub(r'(patchVersion:\s*)\d+', r'\g<1><PATCH>', content)
open('azure-pipeline.yaml', 'w').write(content)
print('Updated azure-pipeline.yaml to <MAJOR>.<MINOR>.<PATCH>')
"
```

Replace `<MAJOR>`, `<MINOR>`, `<PATCH>` with the actual numeric values before running.

Verify the change looks correct:

```bash
grep -E '^\s*(majorVersion|minorVersion|patchVersion):' azure-pipeline.yaml
```

Then commit:

```bash
git add azure-pipeline.yaml
git commit -m "Bump version to <version>"
```

---

## Step 6 — Finish release

```bash
GIT_MERGE_AUTOEDIT=no git flow release finish -m "Release <version>" <version>
```

This will:
1. Merge `release/<version>` into `master`
2. Tag `master` with `<version>`
3. Merge `release/<version>` back into `develop`
4. Delete the release branch

If the finish command fails due to merge conflicts, report the exact error and tell the user to resolve the conflicts manually, then run:
```bash
GIT_MERGE_AUTOEDIT=no git flow release finish -m "Release <version>" <version>
```
again after resolving.

---

## Step 7 — Confirm and push

Show the user a summary:

```
Release <version> is ready locally:
  - master: merged and tagged <version>
  - develop: merged with version bump
  - Tag: <version>
```

Ask: "Ready to push? This will push master, develop, and tags to origin."

If the user confirms, run:

```bash
git push origin master && git push origin develop && git push --tags
```

Report success or any errors.
