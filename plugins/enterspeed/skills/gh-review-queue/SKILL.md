---
name: gh-review-queue
description: Show all open GitHub PRs awaiting your review across all repos. Use this skill whenever the user says "show my review queue", "what PRs do I need to review", "review queue", "PRs waiting for me", "what's in my review queue", "list PRs to review", or "how many PRs do I have to review". Requires the GitHub CLI (gh) to be installed and authenticated.
---

# GitHub Review Queue

Fetches all open pull requests where you are a requested reviewer, grouped by repository.

---

## Step 1: Check prerequisites

Run:

```bash
gh --version
```

If `gh` is not available, tell the user:

> "The GitHub CLI is required. Install it with `brew install gh`, then authenticate with `gh auth login`."

Then stop.

---

## Step 2: Fetch open PRs

Run:

```bash
gh search prs --review-requested=@me --state=open --json number,title,repository,author,updatedAt,isDraft,reviewDecision --limit 100
```

If the command fails, surface the error and suggest:

> "Try running `gh auth status` to check your authentication."

Then stop.

---

## Step 3: Present the queue

If the result is an empty array, say:

> "No open PRs awaiting your review."

Then stop.

Otherwise, group the PRs by `repository.nameWithOwner`. Within each group, sort by `updatedAt` ascending (oldest first — longest-waiting at the top). Sort the groups themselves by the oldest PR in each group.

If the result contains exactly 100 items, append a note at the end:

> "Showing the first 100 results — there may be more. Run `gh search prs --review-requested=@me --state=open --limit 200` to fetch more."

Display in this format (use a markdown table per group so the layout renders predictably across clients):

```
N PRs awaiting your review

### org/repo-name

| # | Title | Author | Age | Review state |
|---|-------|--------|-----|--------------|
| #123 | Fix auth token expiry bug | alice | 2d ago | — |
| #118 | Add dark mode support [draft] | bob | 5d ago | changes requested |

### another-org/other-repo

| # | Title | Author | Age | Review state |
|---|-------|--------|-----|--------------|
| #45 | Upgrade dependencies to v3 | carol | 1d ago | — |
```

**Per-row fields:**
- PR number: `#N`
- Title: truncate to 50 characters with `…` if longer; if `isDraft` is true, append `[draft]` after the (already-truncated) title — the badge is not counted toward the 50-character limit
- Author: the `author.login` value
- Age: human-readable time since `updatedAt` — use the largest appropriate unit (e.g. `3h ago`, `2d ago`, `1w ago`, `3mo ago`)
- Review state: map `reviewDecision` to a human-readable label — `APPROVED` → `approved`, `CHANGES_REQUESTED` → `changes requested`, `REVIEW_REQUIRED` or `null` → `—`

At the end, add a single hint line:

> To open a PR in the browser: `gh pr view <number> --repo <org/repo> --web`
