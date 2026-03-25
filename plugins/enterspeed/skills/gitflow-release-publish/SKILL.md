---
name: gitflow-release-publish
description: Push a prepared git flow release branch and open a PR to master. Use when the user says "publish the release", "push the release branch", "open the PR", or after gitflow-release-start completes. Requires the release branch to already exist locally with the version commit. Follow up with gitflow-release-finish once the master PR is merged.
---

# Git Flow Release — Publish

Pushes the local release branch to GitHub and opens a PR to master (production merge). The back-merge to develop happens later in **gitflow-release-finish**, after the master PR is merged — this ensures both branches share the same merge history and avoids conflicts caused by divergent commit SHAs.

Run **gitflow-release-start** first to create the branch and version commit.

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

Verify the GitHub CLI is installed:

```bash
gh --version
```

If not installed, stop and tell the user:

> "GitHub CLI (`gh`) is not installed. Install it with `brew install gh` and authenticate with `gh auth login` first."

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

Open the production merge PR:

```bash
gh pr create \
  --base master \
  --head "release/$VERSION" \
  --title "Release $VERSION" \
  --body "## Release $VERSION

Bumps version to \`$VERSION\` in \`$PIPELINE_FILE\`.

### Checklist
- [ ] Version variables updated correctly in \`$PIPELINE_FILE\`
- [ ] CI passes on the release branch
- [ ] Reviewed and approved"
```

Capture the PR URL from the command output. Extract the PR number from the URL (the last path segment).

If this fails, stop and report the error.

---

## Done

Show the user the PR URL, then say:

> "Master PR is open: `$MASTER_PR_URL` (#`$MASTER_PR_NUMBER`)
>
> Once it's merged, run **gitflow-release-finish** with version `$VERSION` and master PR `#$MASTER_PR_NUMBER`. The back-merge to develop will be handled as part of the finish step."

---

## If something goes wrong

- **Before the PR is merged**: close the PR on GitHub, then delete the remote and local release branch:

  ```bash
  git push origin --delete "release/$VERSION"
  git branch -D "release/$VERSION"
  ```

  The release is fully undone with no impact on master or develop.
