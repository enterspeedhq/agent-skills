---
name: pr-submit-review
description: Submit a GitHub PR review — approve, request changes, or comment. Use this skill whenever the user says "approve PR", "request changes on PR", "submit my review", "post a review", "approve this PR", "reject this PR", "leave a comment on the PR", or asks to publish feedback on a pull request. Requires the GitHub CLI (gh). Must be run from inside a git repository.
---

# PR Review Submitter

Submits a formal GitHub review on a pull request — approve, request changes, or comment — using the GitHub CLI.

---

## Step 1: Resolve intent

Extract from the user's message:

| Parameter | How to resolve |
|-----------|----------------|
| **PR number** | From the message, or ask if missing |
| **Action** | `approve`, `request-changes`, or `comment` — infer from phrasing (see below) |
| **Body** | From the conversation context (e.g. output of the `pr-review` skill), or ask |

### Mapping phrases to actions

| What the user says | Action |
|--------------------|--------|
| "approve", "looks good", "LGTM" | `--approve` |
| "request changes", "needs work", "not ready", "reject" | `--request-changes` |
| "comment", "leave a note", "just comment", "no verdict" | `--comment` |

If the action is ambiguous, ask before proceeding.

---

## Step 2: Draft the review body

If the conversation already contains a PR review (from the `pr-review` skill or the user's own notes), use that as the source. Otherwise ask the user what they want to say.

### When to approve vs. request changes (Google Engineering Practices)

**Approve** when the change improves overall code health, even if it isn't perfect. A PR doesn't need to be flawless — it needs to be incrementally better. Approve with `nitpick:` or `suggestion (non-blocking):` comments when issues are minor.

**Request changes** only when:
- The change would worsen overall code health, or
- The feature itself is undesirable for the system

Do not block on style preferences that aren't covered by the team's style guide. If something is worth noting but not blocking, use `--comment` instead.

### Body guidelines by action

**Approve** — Keep it short. State what looks good and call out any non-blocking suggestions inline. A sentence or two is enough.

**Request changes** — Be concise and actionable. List only what *must* be fixed before merge, using bullet points. Do not repeat the full review — just the blockers. Prefix each item with a Conventional Comments label where helpful (e.g. `issue (blocking):`).

**Comment** — Use when the verdict isn't clear yet, the review is informational, or you want to leave notes without blocking or approving. Freeform; match length to the content.

### Formatting

When showing the preview in chat, wrap lines at ~80 characters for
readability. When submitting via `gh`, use clean markdown without hard
line breaks — GitHub renders the body as markdown and hard wraps
will appear as unintended line breaks.

---

## Step 3: Show and confirm

Display the exact command you will run and the body text:

```
Action:  approve / request-changes / comment
PR:      #<number>
Body:
---
<body text>
---

Submit this review? (yes / edit body / cancel)
```

Do not proceed until the user confirms. Reviews are visible to the whole team and cannot be unsent.

---

## Step 4: Submit

Run the confirmed command:

```bash
# Approve
gh pr review <number> --approve --body "<body>"

# Request changes
gh pr review <number> --request-changes --body "<body>"

# Comment
gh pr review <number> --comment --body "<body>"
```

Confirm success and show the URL returned by `gh`.
