---
name: gitflow-release-finish
description: Finish a git flow release once the master PR is merged: verifies PR state, tags master, opens a back-merge PR into develop, and cleans up the release branch. Use when the user says "finish the release", "the master PR is merged", "after merging the PR", or "tag the release". Always run after gitflow-release-publish. This is the final step in the release workflow.
---

# Git Flow Release — Finish

Completes the release after the master PR (opened by **gitflow-release-publish**) has been merged. Verifies the merge, tags master, opens a back-merge PR into develop, and cleans up the release branch.

The back-merge must give develop **master's exact merge commit** — that is what keeps the two branches' histories aligned. A PR opened from the *release* branch instead would put different commit SHAs on develop and conflict on every future release.

So the back-merge branches off master and opens the PR from there. It is deliberately **not** opened with `--head master`: that shape works, but GitHub's post-merge **Delete branch** button deletes a PR's *head* branch — which would be master. A disposable `backmerge/<version>` branch carries the same commits and makes that button harmless.

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

## Step 3 — Open the back-merge PR (`backmerge/$VERSION` → develop)

Cut the back-merge branch from master and push it:

```bash
git fetch origin
git checkout -b "backmerge/$VERSION" origin/master
git push -u origin "backmerge/$VERSION"
```

If the branch already exists locally or on the remote, a previous run got this far. Don't force
anything — tell the user it exists, and ask whether to reuse it (`git checkout "backmerge/$VERSION"`)
or delete and recreate it. Wait for their answer.

Open the PR:

```bash
gh pr create \
  --base develop \
  --head "backmerge/$VERSION" \
  --title "Back-merge release $VERSION into develop" \
  --body "## Back-merge release $VERSION

Brings master's release merge commit into develop so both branches share history. No new work — every
commit here was already reviewed on the master PR.

### Checklist
- [ ] No conflicts with develop
- [ ] CI passes
- [ ] Merge using **Create a merge commit** only — do not squash or rebase (a squash would put a
      different SHA on develop, which is the thing this PR exists to prevent)"
```

Capture the PR URL and number from the output.

If PR creation fails, stop and tell the user:

> "Failed to create the back-merge PR. The release is tagged on master (`$VERSION`) and the branch
> `backmerge/$VERSION` is pushed, but develop has not been updated yet. You can open it manually
> (base: `develop`, head: `backmerge/$VERSION`) or re-run:
> `gh pr create --base develop --head backmerge/$VERSION --title 'Back-merge release $VERSION into develop'`"

---

## Step 4 — Get the back-merge merged

No commit here is new work — all of it was reviewed on the master PR — so don't
park this on a human unless the repo or a failure forces it. Some repos do require an approval on
develop regardless; step 4 below covers that. Work down this list:

**1. Are there any checks?**

```bash
gh pr checks "$DEVELOP_PR_NUMBER"
```

If it reports no checks at all, merge straight away:

```bash
gh pr merge "$DEVELOP_PR_NUMBER" --merge
```

**2. If there are checks, queue the merge instead of waiting for them:**

```bash
gh pr merge "$DEVELOP_PR_NUMBER" --auto --merge
```

GitHub merges it as soon as the required checks pass, however long they take. Prefer this — it costs
one command and can't time out.

**3. If `--auto` is refused** (the repo doesn't have auto-merge enabled), watch the checks instead.
Run this **in the background** — CI can outlast a foreground command's limit:

```bash
gh pr checks "$DEVELOP_PR_NUMBER" --watch --fail-fast
```

When it reports success, merge with `gh pr merge "$DEVELOP_PR_NUMBER" --merge`. If it reports a
failure, **stop** — name the failing check and tell the user develop has not been updated yet. Don't
retry and don't merge past a red check.

**4. If a merge is refused for want of an approval**, that's branch protection on develop doing its
job, not an error. Say so plainly: the PR is open and correct, and it needs one approval before it can
merge. Name the two ways forward — someone approves it (`--auto` then merges it unattended, so nothing
further is needed from you), or a repo admin merges it directly. **Don't suggest bypassing protection,
and don't retry the merge in a loop.** If `--auto` was already queued, there is nothing else to run:
tell the user the release completes on its own once the approval lands, and give them the Step 5
verification command to run afterwards.

Never pass `--delete-branch` to any of these. From inside a worktree it tries to switch that worktree
onto another branch, fails, and silently skips deleting anything. Step 5 removes the branch explicitly.

If the merge is refused because of conflicts, **stop**. Tell the user which files conflict and that
they need resolving on `backmerge/$VERSION` before the PR can merge. Don't attempt to resolve them.

---

## Step 5 — Verify the back-merge and clean up

Confirm the PR merged:

```bash
gh pr view "$DEVELOP_PR_NUMBER" --json state --jq '.state'
```

Must return `MERGED`.

If it returns `OPEN` and the merge was queued with `--auto`, that is expected rather than a failure —
it is waiting on checks, or on an approval. Don't wait for it and don't re-run the merge. Tell the
user the release finishes on its own, hand them the verification commands below to run once it lands, and stop
here. The tag is already on master, so nothing is half-done.

If it returns `OPEN` with nothing queued, stop and ask the user to merge it first.

Then verify what actually matters — that develop now contains master:

```bash
git fetch origin
git merge-base --is-ancestor origin/master origin/develop && echo "develop contains master" || echo "develop does NOT contain master"
```

If develop does **not** contain master, stop and report it. The PR state says merged, so this means
it was squashed or rebased rather than merged — develop has equivalent changes under different SHAs,
and the next release will conflict. Tell the user plainly, and that fixing it means merging master
into develop again with a real merge commit.

Update the local branch and remove the branches that have served their purpose:

```bash
git checkout develop && git pull origin develop
git push origin --delete "backmerge/$VERSION"
git branch -D "backmerge/$VERSION"
```

If either delete fails because the branch is already gone, that's fine — say so and continue.

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
Release $VERSION:
  - master: updated and tagged $VERSION
  - Tag $VERSION: pushed to origin
  - develop: <back-merged via PR #N | back-merge PR #N queued, merges when its requirements are met>
  - Branches: <release/$VERSION and backmerge/$VERSION deleted | cleaned up once the back-merge lands>
```

Report only what actually happened. If the back-merge PR is still queued, say so on that line and
say the release is not finished yet — the tag is on master, and develop follows once the PR merges.
Don't print "complete" over a queued merge.

---

## If something went wrong

> **Tip**: If you encounter git flow setup issues, run the **gitflow-prerequisites** skill to verify your environment.

- **Master PR merged but back-merge PR has conflicts**: resolve them in the GitHub conflict editor or check out develop locally, merge master, resolve, and push. Do not skip the back-merge — it keeps the branches in sync for future releases.
- **After both PRs merge**: the release is complete. If you need to undo it, a revert commit on master is the safest path. Team coordination is required.
- **Tag push fails**: check that you have push access and the tag doesn't already exist on the remote (`git ls-remote --tags origin <version>`).
- **Tag pushed incorrectly**: to delete a pushed tag, run `git push origin --delete <version>` and recreate it on the correct commit.
