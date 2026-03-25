---
name: gitflow-release-finish
description: Finish a git flow release once the master PR is merged: verifies PR state, tags master, opens a back-merge PR from master to develop, and cleans up the release branch. Use when the user says "finish the release", "the master PR is merged", "after merging the PR", or "tag the release". Always run after gitflow-release-publish. This is the final step in the release workflow.
---

# Git Flow Release — Finish

Completes the release after the master PR (opened by **gitflow-release-publish**) has been merged. Verifies the merge, tags master, opens a back-merge PR from master to develop, and cleans up the release branch.

The back-merge PR uses **master → develop** (not release → develop). This is critical — it ensures develop receives master's exact merge commit, keeping both branches' histories synchronized. Opening a separate PR from the release branch to develop would create divergent commit SHAs, causing merge conflicts in future releases.

> **Stop on any error** — if any step fails unexpectedly, report the full error output to the user and do not proceed to the next step.

---

## Prerequisites

Ask the user for:

- The **version** that was released (e.g. `1.53.0` — digits only, no `v` prefix)
- The **master PR number** from the gitflow-release-publish output

Validate the version format and store all values in shell variables:

```bash
VERSION="<version>"
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Invalid version format. Must be N.N.N (e.g., 1.53.0, not v1.53.0)"
  exit 1
fi

MASTER_PR="<master-pr-number>"
```

If validation fails, reject and re-prompt for the correct format. Use these variables (`$VERSION`, `$MASTER_PR`) throughout all subsequent steps.

---

## Step 1 — Verify master PR is merged

```bash
gh pr view "$MASTER_PR" --json state --jq '.state'
```

Must return `MERGED`. If it returns `OPEN`, stop and tell the user:

> "PR #`$MASTER_PR` is not merged yet. Merge it on GitHub first. Once merged, re-run this skill."

If it returns `CLOSED` (abandoned/rejected), stop and tell the user:

> "PR #`$MASTER_PR` was closed without merging. Investigate what happened — this workflow cannot be recovered automatically. Consult your team before proceeding."

---

## Step 2 — Pull master and tag

```bash
git checkout master && git pull origin master
```

If this fails, stop and report the error.

### Tag creation decision tree

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

```bash
git ls-remote --tags origin "$VERSION"
```

If this returns nothing, stop and tell the user:

> "Tag `$VERSION` was not found on the remote. The push may have failed. Check your permissions and network connection, then try pushing again with `git push origin $VERSION`."

---

## Step 3 — Open back-merge PR (master → develop)

This step merges master into develop via a PR, so develop receives the exact merge commit from the master PR. This keeps both branches' histories aligned.

```bash
gh pr create \
  --base develop \
  --head master \
  --title "Back-merge release $VERSION into develop" \
  --body "## Back-merge release $VERSION

Merges master into develop after the \`$VERSION\` release. This keeps both branches in sync by giving develop the same merge commit that landed on master.

### Checklist
- [ ] No conflicts with develop
- [ ] CI passes"
```

Capture the PR URL from the command output. Extract the PR number from the URL (the last path segment).

If this fails, stop and tell the user:

> "Failed to create the back-merge PR. The release is tagged on master (`$VERSION`), but develop has not been updated yet. You can create the PR manually on GitHub (base: develop, head: master) or run: `gh pr create --base develop --head master --title 'Back-merge release $VERSION into develop'`"

Tell the user:

> "Back-merge PR is open: `$DEVELOP_PR_URL` (#`$DEVELOP_PR_NUMBER`). Please merge it to sync develop with master. Let me know once it's merged so I can finish the cleanup."

Wait for the user to confirm the develop PR is merged before continuing. Do not proceed to Step 4 until confirmed.

---

## Step 4 — Verify back-merge and clean up

Verify the develop PR is merged:

```bash
gh pr view "$DEVELOP_PR_NUMBER" --json state --jq '.state'
```

Must return `MERGED`. If not, stop and ask the user to merge it first.

Pull develop:

```bash
git checkout develop && git pull origin develop
```

Delete the local release branch if it still exists:

```bash
git branch --list "release/$VERSION"
```

If it returns output:

```bash
git branch -D "release/$VERSION"
```

---

## Done

Show the user a final summary:

```
Release $VERSION complete:
  - master: updated and tagged $VERSION
  - develop: back-merged from master (via PR #$DEVELOP_PR_NUMBER)
  - Local release branch: deleted
  - Tag $VERSION: pushed to origin
```

---

## If something went wrong

> **Tip**: If you encounter git flow setup issues, run the **gitflow-prerequisites** skill to verify your environment.

- **Master PR merged but back-merge PR has conflicts**: resolve them in the GitHub conflict editor or check out develop locally, merge master, resolve, and push. Do not skip the back-merge — it keeps the branches in sync for future releases.
- **After both PRs merge**: the release is complete. If you need to undo it, a revert commit on master is the safest path. Team coordination is required.
- **Tag push fails**: check that you have push access and the tag doesn't already exist on the remote (`git ls-remote --tags origin <version>`).
- **Tag pushed incorrectly**: to delete a pushed tag, run `git push origin --delete <version>` and recreate it on the correct commit.
