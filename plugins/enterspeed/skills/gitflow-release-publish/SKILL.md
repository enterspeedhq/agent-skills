---
name: gitflow-release-publish
version: 1.0.0
description: Push a prepared git flow release branch and open PRs to master and develop. Use when the user says "publish the release", "push the release branch", "open the PRs", or after gitflow-release-start completes. Requires the release branch to already exist locally with the version commit. Follow up with gitflow-release-finish once both PRs are merged.
---

# Git Flow Release — Publish

Pushes the local release branch to GitHub and opens two PRs: one to master (production merge) and one to develop (back-merge). Run **gitflow-release-start** first to create the branch and version commit.

> **Stop on any error** — if any step fails unexpectedly, report the full error output to the user and do not proceed to the next step.

---

## Input

Ask the user for the version being released (e.g. `1.53.0`). Validate it matches the pattern `N.N.N` before continuing. Use this as `<version>` for all subsequent steps.

---

## Prerequisites check

Verify the GitHub CLI is installed:

```bash
gh --version
```

If not installed, stop and tell the user:
> "GitHub CLI (`gh`) is not installed. Install it with `brew install gh` and authenticate with `gh auth login` first."

Verify the release branch exists locally:

```bash
git branch --list "release/<version>"
```

If it returns nothing, stop and tell the user:
> "No local branch `release/<version>` found. Run **gitflow-release-start** with version `<version>` first."

---

## Step 1 — Push release branch

```bash
git push origin release/<version>
```

If this fails, stop and report the error.

---

## Step 2 — Open PR to master

Find the pipeline file name to reference in the PR body:

```bash
ls azure-pipeline.yaml 2>/dev/null || ls azure-pipelines.yaml 2>/dev/null
```

Store as `PIPELINE_FILE`. Open the production merge PR:

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

If this fails, stop and report the error.

---

## Step 3 — Open PR to develop

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

If this fails, stop and report the error.

---

## Done

Show the user both PR URLs, then say:

> "Two PRs are open:
> - **Master PR**: `$MASTER_PR_URL` (#`$MASTER_PR_NUMBER`)
> - **Develop PR**: `$DEVELOP_PR_URL` (#`$DEVELOP_PR_NUMBER`)
>
> Merge the **master PR first**, then the **develop PR**.
>
> Once both are merged, run **gitflow-release-finish** and provide:
> - Version: `<version>`
> - Master PR: `#$MASTER_PR_NUMBER`
> - Develop PR: `#$DEVELOP_PR_NUMBER`"

---

## If something goes wrong

- **Before any PRs are merged**: close both PRs on GitHub, then delete the remote and local release branch:
  ```bash
  git push origin --delete release/<version>
  git branch -D release/<version>
  ```
  The release is fully undone with no impact on master or develop.

- **After master PR merges but before develop PR**: do not skip the back-merge. Merge the develop PR. If it has conflicts, resolve them in the GitHub conflict editor (Edit → resolve conflicts → mark as resolved → commit). If conflicts are too complex for the GitHub editor, check out develop locally, merge master in, resolve, push, then merge the PR.
