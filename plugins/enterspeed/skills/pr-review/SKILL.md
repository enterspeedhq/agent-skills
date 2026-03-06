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

---

## Step 3: Look for best-practice docs in the repo

Search the repo root (and `.github/`) for any of these files. Read any that exist:

- `CONTRIBUTING.md`
- `DEVELOPMENT.md`
- `CODE_STYLE.md`
- `CODING_STANDARDS.md`
- `docs/architecture.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `CLAUDE.md` (team AI conventions)

Note which sections are relevant to the changes in this PR. You will use them to calibrate your review.

---

## Step 4: Read the diff

```bash
gh pr diff <number>
```

Read the full diff. For large diffs (>500 lines), focus on:
1. New files added
2. Core logic changes (skip pure formatting / generated files)
3. Test changes

---

## Step 5: Check out the PR branch (optional but recommended)

```bash
gh pr checkout <number>
```

If the user wants you to run tests or explore the code interactively, check it out. Otherwise the diff is sufficient for the review summary.

---

## Step 6: Deliver the review

Present the review in this structure:

---

### PR #N — [Title]

**Author:** [name] | **Branch:** `[head]` → `[base]` | **Size:** +[additions] / -[deletions] across [N] files

---

#### Summary

2–4 sentences describing what this PR does, why it exists (based on the description and diff), and what it changes at a high level.

---

#### What to pay attention to

A prioritized list of things the reviewer should look at closely. Each item should be specific — reference file names and line ranges where possible.

Review in this priority order (based on Google Engineering Practices):

1. **Design** — Does the overall approach make sense? Does this change belong here? Are component interactions sensible?
2. **Functionality** — Does the code do what it's supposed to? Check edge cases, concurrency issues, and user-facing behavior.
3. **Complexity** — Is anything over-engineered or unnecessarily hard to follow? Watch for premature generalization or unused extensibility.
4. **Tests** — Are there tests? Will they actually fail when the code breaks? Do they cover edge cases, not just the happy path?
5. **Security** — Input validation, auth checks, secrets, SQL injection, XSS, data exposure.
6. **Breaking changes** — API contract changes, schema migrations, removed or renamed fields.
7. **Performance** — N+1 queries, missing indexes, large allocations in hot paths.
8. **Naming** — Are names clear and accurate? Do they communicate intent without being excessively long?
9. **Comments** — Do code comments explain *why*, not *what*? Is anything unclear enough to warrant a comment?
10. **Documentation** — Does any README, guide, or reference doc need updating?
11. **Style / best practices** — Anything that contradicts the repo's own CONTRIBUTING / style docs.

Only include categories where something stands out. Skip the rest.

---

#### Checklist alignment

If a PR template (`.github/PULL_REQUEST_TEMPLATE.md`) exists in the repo, check whether the PR description appears to have addressed each checklist item. Flag any that look unanswered.

---

#### Suggested questions for the author

2–4 open questions to ask the PR author — things that are unclear from the diff alone or that could affect the review decision.

## Comment format

Use **Conventional Comments** labels to make intent unambiguous:

```
<label> [decorations]: <subject>

[optional discussion]
```

| Label | When to use |
|-------|-------------|
| `issue` | Something that must be addressed — correctness, security, breaking change |
| `suggestion` | A concrete improvement proposal — take it or leave it |
| `question` | Genuinely unsure; seeking clarification before forming a view |
| `nitpick` | Trivial preference — style, naming, minor polish |
| `praise` | Call out something done particularly well |
| `thought` | An idea worth considering, no action required |
| `note` | Informational observation, no action required |
| `todo` | A small but necessary change before merge |

Decorations to add in parentheses after the label:
- `(blocking)` — must be resolved before approval
- `(non-blocking)` — can merge, but worth following up
- `(if-minor)` — only act on this if the fix is trivial

Example: `suggestion (non-blocking): Extract this into a helper function — the pattern repeats in three places already.`

---

## Tone (Google Engineering Practices)

- Focus on the code, not the person. "This function is hard to follow" not "you wrote this confusingly."
- Always explain the *why* — developers should understand the reasoning, not just the verdict.
- Approve when the change improves overall code health, even if it isn't perfect. Don't block on style preferences.
- Use `nitpick:` or `suggestion (non-blocking):` for things that aren't worth blocking on.
- Recognize good work — call out clean design, smart test coverage, or a well-named abstraction.
- If code needs a comment to be understood, ask the author to rewrite it rather than just explaining it in the review thread.
