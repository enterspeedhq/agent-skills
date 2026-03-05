---
name: gitflow-release-finish
version: 1.0.0
description: Finish a git flow release after both PRs are merged: verifies PR state, pulls master and develop, deletes the local release branch, creates and pushes the version tag. Use when the user says "finish the release", "both PRs are merged", "release is merged", or "tag the release". Always run after gitflow-release-start.
---

# Git Flow Release — Finish

Completes the release after the master and develop PRs (opened by **gitflow-release-start**) have been merged. Verifies both are merged, syncs local branches, deletes the release branch, and pushes the version tag.

> **Stop on any error** — if any step fails unexpectedly, report the full error output to the user and do not proceed to the next step.

---

## Prerequisites

Ask the user for:
- The **version** that was released (e.g. `1.53.0`)
- The **master PR number** and **develop PR number** from the gitflow-release-start output

---

## Step 1 — Verify both PRs are merged

Check that the master PR is merged:

```bash
gh pr view <master-pr-number> --json state --jq '.state'
```

Check that the develop PR is merged:

```bash
gh pr view <develop-pr-number> --json state --jq '.state'
```

Both must return `MERGED`. If either returns `OPEN` or `CLOSED`, stop and tell the user:
> "PR #`<number>` doesn't appear to be merged yet. Please merge it on GitHub and let me know when done."

---

## Step 2 — Pull updated branches

```bash
git checkout master && git pull origin master
git checkout develop && git pull origin develop
```

If either command fails, stop and report the error.

---

## Step 3 — Delete local release branch

The remote release branch was deleted by GitHub on merge. Delete the local copy with `-D` (git won't recognise it as merged since GitHub handled the merge):

```bash
git branch -D release/<version>
```

---

## Step 4 — Tag and push

Check that the tag does not already exist:

```bash
git tag -l "<version>"
```

If the tag already exists, tell the user and skip tag creation. Otherwise, tag the master HEAD and push:

```bash
git tag <version> $(git rev-parse master)
git push origin <version>
```

---

## Done

Show the user a final summary:

```
Release <version> complete:
  - master: updated and tagged <version>
  - develop: back-merged
  - Local release branch: deleted
  - Tag <version>: pushed to origin
```

---

## If something went wrong

- **After both PRs merge**: the release is complete. If you need to undo it, a revert commit on master is the safest path. Team coordination is required.
- **Tag push fails**: check that you have push access and the tag doesn't already exist on the remote (`git ls-remote --tags origin <version>`).
