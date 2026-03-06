---
name: gitflow-release-finish
version: 1.2.0
description: Finish a git flow release once both PRs are merged: verifies PR state, pulls master and develop, deletes the local release branch, creates and pushes the version tag. Use when the user says "finish the release", "once both PRs are merged", "after merging the PRs", or "tag the release". Always run after gitflow-release-publish. This is the final step in the release workflow.
---

# Git Flow Release — Finish

Completes the release after the master and develop PRs (opened by **gitflow-release-publish**) have been merged. Verifies both are merged, syncs local branches, deletes the release branch, and pushes the version tag.

> **Stop on any error** — if any step fails unexpectedly, report the full error output to the user and do not proceed to the next step.

---

## Prerequisites

Ask the user for:

- The **version** that was released (e.g. `1.53.0` — digits only, no `v` prefix)
- The **master PR number** and **develop PR number** from the gitflow-release-publish output

Validate the version format and store all values in shell variables:

```bash
VERSION="<version>"
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Invalid version format. Must be N.N.N (e.g., 1.53.0, not v1.53.0)"
  exit 1
fi

MASTER_PR="<master-pr-number>"
DEVELOP_PR="<develop-pr-number>"
```

If validation fails, reject and re-prompt for the correct format. Use these variables (`$VERSION`, `$MASTER_PR`, `$DEVELOP_PR`) throughout all subsequent steps.

---

## Step 1 — Verify both PRs are merged

Check that the master PR is merged:

```bash
gh pr view "$MASTER_PR" --json state --jq '.state'
```

Check that the develop PR is merged:

```bash
gh pr view "$DEVELOP_PR" --json state --jq '.state'
```

Both must return `MERGED`. If either returns `OPEN`, stop and tell the user:

> "PR #`$MASTER_PR` (or `#$DEVELOP_PR`) is not merged yet. Merge it on GitHub first. Once merged, you can re-run this skill with the same PR numbers."

If either returns `CLOSED` (abandoned/rejected), stop and tell the user:

> "PR #`$MASTER_PR` (or `#$DEVELOP_PR`) was closed without merging. You'll need to investigate what happened. This workflow cannot be recovered automatically — consult your team before proceeding."

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
git branch --list "release/$VERSION"
```

If it returns output, delete it with `-D` (force delete is required because the remote deletion doesn't update the local tracking ref automatically):

```bash
git branch -D "release/$VERSION"
```

If it returns nothing, the branch was already deleted locally — continue to Step 4.

---

## Step 4 — Tag and push

Confirm you are on master before tagging:

```bash
git rev-parse --abbrev-ref HEAD
```

If the output is not `master`, run `git checkout master` first.

### Tag creation decision tree

Follow this logic to create or verify the tag:

1. **Check if tag exists locally:**

   ```bash
   git tag -l "$VERSION"
   ```

2. **If tag does NOT exist** → Create and push it:

   ```bash
   git tag "$VERSION" master
   git push origin "$VERSION"
   ```

   Then skip to "Verify tag on remote" below.

3. **If tag DOES exist** → Verify it points to master HEAD:

   ```bash
   git rev-parse "$VERSION"
   git rev-parse master
   ```

   - **If they match** → Tag is correct. Check if it's on remote:
     ```bash
     git ls-remote --tags origin "$VERSION"
     ```

     - If on remote → Skip push (already published)
     - If not on remote → Push it: `git push origin "$VERSION"`
   - **If they don't match** → Stop and tell the user:
     > "Tag `$VERSION` already exists locally but points to a different commit than master HEAD. Investigate before proceeding — do not overwrite the tag."

### Verify tag on remote

Confirm the tag exists on GitHub:

```bash
git ls-remote --tags origin "$VERSION"
```

If this returns nothing, stop and tell the user:

> "Tag `$VERSION` was not found on the remote. The push may have failed. Check your permissions and network connection, then try pushing again with `git push origin $VERSION`."

---

## Done

Show the user a final summary:

```
Release $VERSION complete:
  - master: updated and tagged $VERSION
  - develop: back-merged (via develop PR merge)
  - Local release branch: deleted
  - Tag $VERSION: pushed to origin
```

> **Note**: The back-merge to develop was completed when you merged the develop PR on GitHub. No additional merge step is needed.

---

## If something went wrong

> **Tip**: If you encounter git flow setup issues, run the **gitflow-prerequisites** skill to verify your environment.

- **After both PRs merge**: the release is complete. If you need to undo it, a revert commit on master is the safest path. Team coordination is required.
- **Tag push fails**: check that you have push access and the tag doesn't already exist on the remote (`git ls-remote --tags origin <version>`).
- **Tag pushed incorrectly**: to delete a pushed tag, run `git push origin --delete <version>` and recreate it on the correct commit.
