---
name: pr-review
description: Review a pull request in the current git repository. Use this skill whenever the user says "review PR", "review pull request", "check PR #N", "look at PR", "give me a PR review", or provides a PR number and asks for feedback. Requires the GitHub CLI (gh) to be installed. Must be run from inside a git repository.
---

# PR Reviewer

Checks out a pull request, reads the diff and any repo best-practice docs, then delivers a structured review summary and focused attention points.

---

## Step 1: Resolve the PR number

Extract the PR number from the user's message. If it is not provided, ask:

> "Which PR number should I review?"

---

## Step 2: Fetch PR metadata

Run these commands in the current working directory:

```bash
# Full PR details (title, body, author, branch, state, labels, review requests)
gh pr view <number> --json title,body,author,headRefName,baseRefName,state,labels,reviewRequests,additions,deletions,changedFiles

# List of changed files with status
gh pr diff <number> --name-only
```

If `gh` is not available, tell the user to install the GitHub CLI (`brew install gh` / `gh auth login`) and stop.

If the PR cannot be fetched (not found, already deleted, or permission denied), explain the error clearly and suggest the user verify the PR number and that they have access to the repository.

**Story lookup:** Attempt to extract a Shortcut story ID by matching the pattern `sc-\d+` in `headRefName`.

If not found there, scan the PR body and comments for the same pattern:

```bash
gh pr view <number> --json body,comments
```

If no match anywhere, skip all story steps silently. Do not mention it.

If a story ID is found, call `stories-get-by-id` with the numeric part of the ID:

- If the Shortcut MCP tool is unavailable or returns an error for any reason: skip silently, proceed as today
- If the story is found: store the title, description, and acceptance criteria for use in Step 7

---

## Step 3: Look for best-practice docs in the repo

Search the repo root (and `.github/`) for any of these files. Read any that exist:

- `CONTRIBUTING.md`
- `DEVELOPMENT.md`
- `CODE_STYLE.md`
- `CODING_STANDARDS.md`
- `docs/architecture.md`
- `docs/architecture/` (any `.md` files within)
- `docs/*-guidelines.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `CLAUDE.md` (team AI conventions)

Note which sections are relevant to the changes in this PR. You will use them to calibrate your review. If none of these files exist, proceed without them — just review the diff against general engineering practices.

---

## Step 4: Check out the PR branch

```bash
gh pr checkout <number>
```

Check out the branch to get full file context. This enables relative path resolution for subsequent git commands, lets you navigate code beyond the diff (callers, related modules, tests), and makes the branch available in the IDE if the user wants to explore interactively.

Skip only if the user explicitly says they just want a quick diff-based summary. If checkout fails (local branch conflict, network issue), proceed with diff-only review and note this to the user.

---

## Step 5: Check for pre-flight log

With the branch checked out, look for a file matching `.pre-flight/<head-branch>*.md`:

```bash
ls .pre-flight/<head-branch>* 2>/dev/null
```

If no log exists, note it once in the review output:

> `note:` No pre-flight log found for this branch. The author may not have run a self-check before raising this PR.

Do not block, flag, or repeat this. One line, move on.

---

## Step 6: Analyze changes strategically

First, get the overview of what changed:

```bash
git diff --name-status origin/<base-branch>...HEAD
git diff --stat origin/<base-branch>...HEAD
```

The status shows which files were added (A), modified (M), or deleted (D). The stat shows line counts per file.

**For small PRs** (≤5 files AND ≤200 total line changes):

Read the full diff — it's efficient and gives complete context:

```bash
git diff origin/<base-branch>...HEAD
```

**For larger PRs**, use targeted reading to minimize token cost:

1. **New files (status `A`)**: Read the entire file with `read_file` — you need full context
2. **Modified files (status `M`)**:
   - If changes are small (<50 lines per file), read the file-specific diff:
     ```bash
     git diff origin/<base-branch>...HEAD -- path/to/file
     ```
   - If changes are large (50+ lines), read the full file with `read_file` to understand the broader context
3. **Deleted files (status `D`)**: Note the removal; no content needed
4. **Focus on core changes**: Skip generated files (package-lock.json, .min.js, etc.), pure formatting commits, and test fixtures unless they're central to the PR

This approach balances completeness with efficiency. For a 10-file PR with 800 lines changed, targeted reading can reduce token cost by 40-60% compared to reading the full diff.

If doing a focused review due to PR size, say so explicitly in the summary: "Large PR — review focused on [specific areas]; [what was skipped] were not examined in detail."

---

## Step 7: Deliver the review

Use **Conventional Comments** labels throughout to make intent unambiguous (full reference in the Comment format section below). Each observation should be prefixed with the appropriate label, e.g. `issue (blocking):`, `suggestion (non-blocking):`, `nitpick:`.

Present the review in this structure:

---

### PR #N — [Title]

**Author:** [name] | **Branch:** `[head]` → `[base]` | **Size:** +[additions] / -[deletions] across [N] files
_(If a story was fetched: `Story: sc-XXXX — [title]`)_

---

#### Summary

2–4 sentences describing what this PR does, why it exists (based on the description and diff), and what it changes at a high level.

If a story was fetched: add a sentence on story alignment — does the diff appear to address the story goal and acceptance criteria? If there are apparent gaps, surface them as `question (non-blocking):` items under "What to pay attention to". If the PR title or description doesn't reflect the story, raise as `suggestion (non-blocking):`.

---

#### What to pay attention to

A list of things the reviewer should look at closely. Each item should be specific — reference file names and line ranges where possible.

Consider these categories in rough priority order, but focus on what matters most to this PR (based on Google Engineering Practices):

1. **Design** — Does the overall approach make sense? Does this change belong here? Are component interactions sensible? Look for hardcoded constants that may need to vary by environment or behave differently between on-premise and multi-tenancy SaaS deployments.
2. **Functionality** — Does the code do what it's supposed to? Check edge cases, concurrency issues, and user-facing behavior.
3. **Complexity** — Is anything over-engineered or unnecessarily hard to follow? Watch for premature generalization or unused extensibility.
4. **Tests** — Are there tests? Will they actually fail when the code breaks? Do they cover edge cases, not just the happy path?
5. **Security** — Input validation, auth checks, secrets, SQL injection, XSS, data exposure.
6. **Breaking changes** — API contract changes, schema migrations, removed or renamed fields.
7. **Performance** — N+1 queries, missing indexes, large allocations in hot paths.
8. **Naming** — Are names clear and accurate? Do they communicate intent without being excessively long?
9. **Comments** — Do code comments explain _why_, not _what_? Is anything unclear enough to warrant a comment?
10. **Documentation** — Does any README, guide, or reference doc need updating?
11. **Style / best practices** — Anything that contradicts the repo's own CONTRIBUTING / style docs.

Only include categories where something stands out. Skip the rest.

---

#### Checklist alignment

If a PR template (`.github/PULL_REQUEST_TEMPLATE.md`) exists in the repo, check whether the PR description appears to have addressed each checklist item:

- **Unanswered / skipped** — flag as `question (non-blocking):` and ask the author to confirm intentionality
- **Clearly violated** (e.g. checklist says "tests required" and there are none) — flag as `issue (blocking):`

---

#### Suggested questions for the author

2–4 open questions to ask the PR author — things that are unclear from the diff alone or that could affect the review decision.

## Comment format

Use **Conventional Comments** labels to make intent unambiguous:

```
<label> [decorations]: <subject>

[optional discussion]
```

| Label        | When to use                                                               |
| ------------ | ------------------------------------------------------------------------- |
| `issue`      | Something that must be addressed — correctness, security, breaking change |
| `suggestion` | A concrete improvement proposal — take it or leave it                     |
| `question`   | Genuinely unsure; seeking clarification before forming a view             |
| `nitpick`    | Trivial preference — style, naming, minor polish                          |
| `praise`     | Call out something done particularly well                                 |
| `thought`    | An idea worth considering, no action required                             |
| `note`       | Informational observation, no action required                             |
| `todo`       | A small but necessary change before merge                                 |

Decorations to add in parentheses after the label:

- `(blocking)` — must be resolved before approval
- `(non-blocking)` — can merge, but worth following up
- `(if-minor)` — only act on this if the fix is trivial

Example: `suggestion (non-blocking): Extract this into a helper function — the pattern repeats in three places already.`

---

## Tone (Google Engineering Practices)

- Focus on the code, not the person. "This function is hard to follow" not "you wrote this confusingly."
- Always explain the _why_ — developers should understand the reasoning, not just the verdict.
- Approve when the change improves overall code health, even if it isn't perfect. Don't block on style preferences.
- Use `nitpick:` or `suggestion (non-blocking):` for things that aren't worth blocking on.
- Recognize good work — call out clean design, smart test coverage, or a well-named abstraction.
- If code needs a comment to be understood, ask the author to rewrite it rather than just explaining it in the review thread.
