---
name: pr-submit-review
version: 1.0.0
description: Submit a GitHub PR review — approve, request changes, or comment. Use this skill whenever the user says "approve PR", "request changes on PR", "submit my review", "post a review", "approve this PR", "reject this PR", "leave a comment on the PR", or asks to publish feedback on a pull request. Requires the GitHub CLI (gh). Must be run from inside a git repository.
---

# PR Review Submitter

Submits a formal GitHub review on a pull request — approve, request changes, or comment — using the GitHub CLI.

---

## Step 1: Extract parameters

Extract from the user's message:

| Parameter | How to resolve |
|-----------|----------------|
| **PR number** | From the message, or ask if missing |
| **Action** | `approve`, `request-changes`, or `comment` — infer from phrasing (see below) |
| **Body** | Check for prior review notes in the conversation. If none exist, ask the user what they want to say. |

### Mapping phrases to actions

| What the user says | Action |
|--------------------|--------|
| "approve", "looks good", "LGTM" | `--approve` |
| "request changes", "needs work", "not ready", "reject" | `--request-changes` (note: GitHub has no "reject" — this is the closest equivalent) |
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

### Emoji conventions

Use these prefixes to make the review scannable at a glance:

| Label | Emoji |
|-------|-------|
| `issue (blocking):` | 🚫 |
| `issue (non-blocking):` | ⚠️ |
| `suggestion:` | 💡 |
| `nitpick:` | 🔍 |
| `question:` | ❓ |
| `praise:` | ✨ |
| `thought:` | 💭 |

### Review structure

Always order the body as follows, regardless of action type:

1. **Blockers / issues** — what must change (skip section if none)
2. **Suggestions / nitpicks** — non-blocking improvements (skip section if none)
3. **Positives** — what worked well (always include, always substantive)

The positives section is the last thing the author reads — expand on it. Name specific decisions, call out good patterns, or note what made the PR easy to review. One genuine sentence beats three vague ones.

### Markdown formatting

Use H3 headers (`###`) for each section that appears in the body:

```markdown
### 🚫 Blockers
### 💡 Suggestions
### ✨ What worked well
```

Within a section, keep items flat by default. Add an H4 subheading (`####`) only when **2 or more items share the same theme** (e.g. same file area, same concern like "error handling" or "flow logic"). A single item never gets its own subheading.

Example of a grouped section:

```markdown
### 🚫 Blockers

#### Flow handling
- 🚫 `issue (blocking):` The early-return on line 42 skips the cleanup call — this will leak state on error paths.
- 🚫 `issue (blocking):` The loop on line 67 doesn't account for an empty list and will throw.

#### Auth
- 🚫 `issue (blocking):` Token is logged in plain text on line 88.
```

Omit a section header entirely if that section has no content (except Positives, which is always present).

### Body guidelines by action

**Approve** — 1–3 sentences. Lead with any non-blocking suggestions, then close with what specifically made this approvable.

**Request changes** — 3–5 bullets maximum, covering only what *must* be fixed before merge. Prefix each with the relevant emoji label. If the user's draft exceeds 5 blockers, flag it and ask which items are truly blocking before submitting. Always end with a positives section.

**Comment** — Use when the verdict isn't clear yet, or you want to leave notes without blocking or approving. Freeform; match length to the content. Still end with positives if there are any.

### Formatting

When showing the preview in chat, wrap lines at ~80 characters for readability.

When submitting via `gh`, pass the body as a multiline heredoc so newlines are preserved correctly and GitHub renders it as proper markdown:

```bash
gh pr review <number> --approve --body "$(cat <<'EOF'
### 💡 Suggestions

- 💡 `suggestion:` The helper in `utils.ts` could be extracted to a shared module — it's duplicated in two places already.

### ✨ What worked well

Clean separation of concerns in the new service layer, and the test coverage on the edge cases is solid. Easy to follow.
EOF
)"
```

Do not use `\n` escape sequences or collapse the body to a single line — GitHub renders the body as markdown and hard-wrapped single-line strings produce unintended formatting.

---

## Step 3: Show and confirm

Display the exact command you will run and the body text. Auto-detect the repo slug from `gh repo view --json nameWithOwner -q .nameWithOwner`:

```
Action:  <approve / request-changes / comment>   ← one action only
PR:      #<number>
Repo:    <owner/repo>
Body:
---
<body text>
---

Submit this review? (yes / edit body / cancel)
```

Do not proceed until the user confirms. Reviews are visible to the whole team and cannot be unsent.

If the user says **"edit body"**: present the current body and ask what they want to change. Apply their edits, show the updated preview, and ask for confirmation again. Repeat until they confirm or cancel.

---

## Step 4: Submit

Run the confirmed command using a heredoc so multiline markdown is preserved correctly:

```bash
# Approve
gh pr review <number> --approve --body "$(cat <<'EOF'
<body>
EOF
)"

# Request changes
gh pr review <number> --request-changes --body "$(cat <<'EOF'
<body>
EOF
)"

# Comment
gh pr review <number> --comment --body "$(cat <<'EOF'
<body>
EOF
)"
```

Confirm success and show the URL returned by `gh`.

If `gh` is not installed or the user is not authenticated, explain the error and direct them to run `brew install gh && gh auth login`. If the PR number is not found or access is denied, say so clearly and ask the user to verify the number and their repo permissions. If the user lacks review permissions (common on forks or private repos they don't own), note that they may need to be added as a collaborator or use a comment instead.
