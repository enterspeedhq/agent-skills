---
name: gitflow-release-publish
version: 1.1.0
description: Push a prepared git flow release branch and open PRs to master and develop. Use when the user says "publish the release", "push the release branch", "open the PRs", or after gitflow-release-start completes. Requires the release branch to already exist locally with the version commit. Follow up with gitflow-release-finish once both PRs are merged.
---

# Git Flow Release — Publish

Pushes the local release branch to GitHub and opens two PRs: one to master (production merge) and one to develop (back-merge). Run **gitflow-release-start** first to create the branch and version commit.

> **Stop on any error** — if any step fails unexpectedly, report the full error output to the user and do not proceed to the next step.

---

## Input

Ask the user for the version being released (e.g. `1.53.0`). Store it in a shell variable and validate the format:

```bash
VERSION="<version>"
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Invalid version format. Must be N.N.N (e.g. 1.53.0, not v1.53.0)"
  exit 1
fi
```

Reject and re-prompt if invalid. Use `$VERSION` throughout all subsequent steps.

---

## Prerequisites check

Verify the GitHub CLI is installed and `jq` (JSON processor) is available:

```bash
gh --version && jq --version
```

If either is not installed, stop and tell the user:

> "GitHub CLI (`gh`) is not installed. Install it with `brew install gh` and authenticate with `gh auth login` first."
>
> "JSON processor (`jq`) is not installed. Install it with `brew install jq`."

Verify the release branch exists locally:

```bash
git branch --list "release/$VERSION"
```

If it returns nothing, stop and tell the user:

> "No local branch `release/$VERSION` found. Run **gitflow-release-start** with version `$VERSION` first."

---

## Step 1 — Push release branch

```bash
git push origin "release/$VERSION"
```

If this fails, stop and report the error.

---

## Step 2 — Open PR to master

Find the pipeline file name to reference in the PR body:

```bash
PIPELINE_FILE=$(ls azure-pipelines.yaml 2>/dev/null || ls azure-pipelines.yml 2>/dev/null || ls azure-pipeline.yaml 2>/dev/null || ls azure-pipeline.yml 2>/dev/null)
```

If neither file is found, use fallback with brief warning:

```bash
if [ -z "$PIPELINE_FILE" ]; then
  echo "WARNING: Pipeline file not found in current directory."
  PIPELINE_FILE="azure-pipeline.yaml"
fi
```

Open the production merge PR and extract the PR number directly:

```bash
MASTER_PR_NUMBER=$(gh pr create \
  --base master \
  --head "release/$VERSION" \
  --title "Release $VERSION" \
  --body "## Release $VERSION

Bumps version to \`$VERSION\` in \`$PIPELINE_FILE\`.

### Checklist
- [ ] Version variables updated correctly in \`$PIPELINE_FILE\`
- [ ] CI passes on the release branch
- [ ] Reviewed and approved" \
  --json number --jq '.number')
MASTER_PR_URL=$(gh pr view "$MASTER_PR_NUMBER" --json url --jq '.url')
echo "Master PR: $MASTER_PR_URL (#$MASTER_PR_NUMBER)"
```

If this fails, stop and report the error. No PRs have been created yet if you reach this point.

---

## Step 3 — Open PR to develop

```bash
DEVELOP_PR_NUMBER=$(gh pr create \
  --base develop \
  --head "release/$VERSION" \
  --title "Back-merge release $VERSION into develop" \
  --body "## Back-merge release $VERSION

Merges release branch back into develop after the \`$VERSION\` release.

### Checklist
- [ ] No conflicts with develop
- [ ] CI passes" \
  --json number --jq '.number')
DEVELOP_PR_URL=$(gh pr view "$DEVELOP_PR_NUMBER" --json url --jq '.url')
echo "Develop PR: $DEVELOP_PR_URL (#$DEVELOP_PR_NUMBER)"
```

If this fails, you now have one open PR (master) that needs cleanup. Stop and tell the user:

> "Failed to create the develop PR. The master PR (#`$MASTER_PR_NUMBER`) is open. You can either:
>
> 1. Manually create the develop PR on GitHub (base: develop, head: release/$VERSION)
> 2. Close the master PR and retry this skill from the beginning
> 3. Run this command again: `gh pr create --base develop --head release/$VERSION --title 'Back-merge release $VERSION' --body 'Back-merge for $VERSION'`"

---

## Done

Show the user both PR URLs, then say:

> "Two PRs are open:
>
> - **Master PR**: `$MASTER_PR_URL` (#`$MASTER_PR_NUMBER`)
> - **Develop PR**: `$DEVELOP_PR_URL` (#`$DEVELOP_PR_NUMBER`)
>
> **Important**: Merge the **master PR first**, then the **develop PR**. This order ensures that the version changes on master are included in the back-merge to develop.
>
> **Merge strategy**: Use your team's standard merge method (merge commit, squash, or rebase). If you're unsure, ask your team lead.
>
> Once both are merged, run **gitflow-release-finish** and provide:
>
> - Version: `$VERSION`
> - Master PR: `#$MASTER_PR_NUMBER`
> - Develop PR: `#$DEVELOP_PR_NUMBER`
>
> **Note**: Copy these PR numbers now. I don't have persistent memory across sessions, so you'll need to provide them again when running gitflow-release-finish."

> **If something goes wrong**: See the troubleshooting section below for recovery steps.

---

## If something goes wrong

- **Before any PRs are merged**: close both PRs on GitHub, then delete the remote and local release branch:

  ```bash
  git push origin --delete "release/$VERSION"
  git branch -D "release/$VERSION"
  ```

  The release is fully undone with no impact on master or develop.

- **After master PR merges but before develop PR**: do not skip the back-merge. Merge the develop PR. If it has conflicts, resolve them in the GitHub conflict editor (Edit → resolve conflicts → mark as resolved → commit). If conflicts are too complex for the GitHub editor, check out develop locally, merge master in, resolve, push, then merge the PR.
