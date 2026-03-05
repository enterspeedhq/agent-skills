---
name: gitflow-release-finish
version: 1.2.0
description: Finish a git flow release after both PRs are merged: verifies PR state, pulls master and develop, deletes the local release branch, creates and pushes the version tag. Use when the user says "finish the release", "both PRs are merged", "release is merged", or "tag the release". Always run after gitflow-release-publish. This is the final step in the release workflow.
---

# Git Flow Release — Finish

Completes the release after the master and develop PRs (opened by **gitflow-release-publish**) have been merged. Verifies both are merged, syncs local branches, deletes the release branch, and pushes the version tag.

> **Stop on any error** — if any step fails unexpectedly, report the full error output to the user and do not proceed to the next step.

---

## Prerequisites

Ask the user for:

- The **version** that was released (e.g. `1.53.0` — digits only, no `v` prefix)
- The **master PR number** and **develop PR number** from the gitflow-release-publish output

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

Both must return `MERGED`. If either returns `OPEN`, stop and tell the user:

> "PR #`<number>` is not merged. Merge it on GitHub and run this skill again."

If either returns `CLOSED` (abandoned/rejected), stop and tell the user:

> "PR #`<number>` was closed without merging. Please check what happened — you may need to reopen it or open a new PR from `release/<version>`."

---

## Step 2 — Pull updated branches

```bash
git checkout master && git pull origin master
git checkout develop && git pull origin develop
```

If either command fails, stop and report the error.

---

## Step 3 — Delete local release branch

The remote release branch was deleted by GitHub on merge. Check if the local copy still exists before deleting:

```bash
git branch --list "release/<version>"
```

If it returns output, delete it with `-D` (git won't recognise it as merged since GitHub handled the merge):

```bash
git branch -D release/<version>
```

If it returns nothing, the branch was already deleted locally — continue to Step 4.

---

## Step 4 — Tag and push

Confirm you are on master before tagging:

```bash
git rev-parse --abbrev-ref HEAD
```

If the output is not `master`, run `git checkout master` first.

### Check if tag already exists locally

Check that the tag does not already exist:

```bash
git tag -l "<version>"
```

If the tag already exists, do not skip silently — first verify it points to the correct commit:

```bash
git show <version> --oneline
```

If it points to the expected master HEAD, the local tag is correct. Check whether it already exists on the remote:

```bash
git ls-remote --tags origin <version>
```

If it's already on the remote, skip the push — the release tag is already published. If it's not on the remote, push it:

```bash
git push origin <version>
```

If the tag points to a **different** commit, stop and tell the user:

> "Tag `<version>` already exists but points to an unexpected commit. Investigate before proceeding — do not overwrite the tag."

If the tag does not exist at all, create and push it:

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

> **Tip**: If you encounter git flow setup issues, run the **gitflow-prerequisites** skill to verify your environment.

- **After both PRs merge**: the release is complete. If you need to undo it, a revert commit on master is the safest path. Team coordination is required.
- **Tag push fails**: check that you have push access and the tag doesn't already exist on the remote (`git ls-remote --tags origin <version>`).
- **Tag pushed incorrectly**: to delete a pushed tag, run `git push origin --delete <version>` and recreate it on the correct commit.
