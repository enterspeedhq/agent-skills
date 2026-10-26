---
name: pr-review
description: Review a pull request in the current git repository. Use this skill whenever the user says "review PR", "review pull request", "check PR #N", "look at PR", "give me a PR review", or provides a PR number and asks for feedback. Requires the GitHub CLI (gh) to be installed. Must be run from inside a git repository.
---

# PR Reviewer

Checks out a pull request, reads the diff and any repo best-practice docs, then delivers a structured review summary and focused attention points.

> **Important:** All checkout and file-level work happens in a dedicated tmp worktree created specifically for this review (e.g. `/tmp/pr-review-<repo>-<number>`). Steps 2 and 3 run in the current working directory as normal. Never use the primary working directory for checkout — this review must not interfere with other in-progress work.

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
- If the story is found: store the title, description, and acceptance criteria for use in Step 8

**Earlier review rounds.** Read the reviews in full, not `reviewDecision`. That field is a summary that a `COMMENTED` review doesn't change, so it can read `APPROVED` while a later, substantive review sits unread. Most of a round usually lives in the inline comments and the replies under them, which come from a separate endpoint; `gh pr view --json comments` returns neither. Both endpoints return 30 items per page, so paginate:

```bash
gh api user --jq .login
gh api --paginate repos/{owner}/{repo}/pulls/<number>/reviews --jq '.[] | {id, user: .user.login, state, submitted_at, commit_id, body}'
gh api --paginate repos/{owner}/{repo}/pulls/<number>/comments --jq '.[] | {user: .user.login, path, line, in_reply_to_id, created_at, body}'
```

If you have already reviewed this PR, this is round N+1. List what your last review raised, including its inline comments, then check what the author has pushed or replied since. Take the `commit_id` of your last review and find the changes since then:

```bash
git merge-base --is-ancestor <commit_id> HEAD && git diff <commit_id>..HEAD
```

If that commit is no longer an ancestor of `HEAD` (the branch was rebased or force-pushed), that diff would pick up whatever landed on the base in between, so do the full review instead. Otherwise Steps 4–7 cover only that diff, checked against the open items. Don't re-raise points that were settled, and frame the output as "Round N". If you haven't reviewed it before, do the full review.

**CI state.** Run `gh pr checks <number>` and read every row. A check's name may not say everything it runs (a "Build" check can include lint), and one green check says nothing about the others. Mention any failing or pending check in the summary. The exit code is data, not an error: it is `8` while checks are pending and non-zero when one has failed.

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

## Step 4: Create a dedicated worktree for the PR

Derive the repo name from `git remote get-url origin` (take the last path segment, strip `.git`). Use `/tmp/pr-review-<repo>-<number>` as the worktree path throughout — this avoids collisions when reviewing the same PR number in different repositories.

Remove any stale worktree at that path first:

```bash
git worktree remove --force /tmp/pr-review-<repo>-<number> 2>/dev/null || true
```

Then fetch the PR's HEAD and create a detached worktree — this never creates a local branch, so it can't conflict with branches checked out in the primary clone or other worktrees:

```bash
# the PR head must come first: FETCH_HEAD resolves to the first ref fetched
git fetch origin refs/pull/<number>/head refs/heads/<base-branch>:refs/remotes/origin/<base-branch>
git worktree add --detach /tmp/pr-review-<repo>-<number> FETCH_HEAD
```

**Fallback** — if the `pull/<number>/head` ref is unavailable (e.g. a non-GitHub remote):

```bash
git worktree add --detach /tmp/pr-review-<repo>-<number>
cd /tmp/pr-review-<repo>-<number>
gh pr checkout <number> --detach
```

> Note: these commands use bash syntax. Run via bash/zsh — not PowerShell.

Run all subsequent commands (diff, file reads, pre-flight check) from `/tmp/pr-review-<repo>-<number>`.

If the worktree cannot be created, proceed with diff-only review and note this to the user.

---

## Step 5: Check for pre-flight log

With the worktree created, look for the log **pre-flight** writes: `.pre-flight/<YYYY-MM-DD>-<head-branch>.md`, with every `/` in the branch name replaced by `-` (so `feature/sc-1234/foo` becomes `2026-10-22-feature-sc-1234-foo.md`):

```bash
ls .pre-flight/*-$(echo '<head-branch>' | tr / -).md 2>/dev/null
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
4. **Generated and vendored files** (lock files, `.min.js`, build output, migration designer files) may be skipped — with that reason.

This approach balances completeness with efficiency. For a 10-file PR with 800 lines changed, targeted reading can reduce token cost by 40-60% compared to reading the full diff.

**Every changed file is accounted for.** Keep a checklist built from the `--name-status` output — not from what you remember reading — and mark each file `reviewed` or `skipped` with a concrete reason. Targeted reading changes *how* you read a file, never *whether* you read it: agents reviewing large PRs tend to quietly cover some files and drop others, and nobody can tell from the review which ones. If the PR is too large to read every file, say so in the summary and list the skipped files and why.

**Validate findings before writing them up.** Hand your draft findings to two subagents. Each one checks the findings in its own area, and a finding is dropped if either one refutes it:

1. **code** checks findings about the diff itself: correctness, design, tests and naming;
2. **story** checks findings about the story and its ACs (if a story was fetched) and the repo conventions from Step 3.

A subagent confirms a finding by pointing to the code or text that makes it true, and refutes it by showing that code or text says otherwise. Each may also add a finding in its own area, which goes through the same check.

For small PRs (the threshold above), skip the subagents and do the two passes yourself, one after the other. Do the same if subagents aren't available.

When briefing them:

- **One worktree per subagent**, on the same commit as the review worktree, so a push during the review can't put the agents on a different commit. No fetch is needed:
  ```bash
  SHA=$(git -C /tmp/pr-review-<repo>-<number> rev-parse HEAD)
  git worktree add --detach /tmp/pr-review-<repo>-<number>-code "$SHA"
  git worktree add --detach /tmp/pr-review-<repo>-<number>-story "$SHA"
  ```
  Agents sharing a checkout see each other's test merges and scratch files, and report them as problems with the author's branch.
- **Describe disagreements neutrally.** If code and docs disagree, ask "do X and Y agree, and which is right?", not "does X break Y?", which treats Y as the authority. Two passes that share one wrong premise will agree with each other.
- **Treat deleted intent as evidence.** If the diff removes text explaining why something exists, check whether that deletion is right rather than accepting it as tidying.
- **Search at a ref, not the working tree.** Outside the review worktree, use `git grep <pattern> origin/<default> -- <path>` or `git show origin/<default>:<path>`. A local checkout may be parked on an old branch.

---

## Step 7: Check each point against the code

Before writing anything up, check every `issue`, `todo` and `suggestion` you intend to raise against the worktree. Reviews most often go wrong in two ways: the cited line isn't what the comment says it is, or the thing reported "missing" is there under a different name.

1. **Quote the code.** For each point, copy the exact text it is about from the file in the worktree — one to five lines, verbatim, not paraphrased. Then confirm it is really there:
   ```bash
   grep -nF '<the most distinctive line of the quote>' path/to/file
   ```
   Pick a line that can only match once — not `}` or `return null;`. If `grep` still returns several matches, use the one whose surrounding lines match the rest of the quote. Take the line number from `grep`, not from memory. If the quote isn't found, re-read the file: either fix the quote or drop the point.
2. **Point at changed code.** If the quoted line isn't part of this PR's diff, the point is about existing code — raise it as `note:` or `thought:`, not as an `issue` on this PR. The exception is evidence: an untested caller of a method this PR changes is a fair `issue`, anchored on the changed method.
3. **"Missing" needs a search.** For anything reported as absent (no test, no migration, no null check), search for the actual symbol — the class, method or table name — not a guessed filename, and mention the search in the point. A filename pattern that finds nothing proves nothing.
4. **Drop it, or ask it, if you can't show it.** If you can't point to the line that makes a point true, rephrase it as a `question` or leave it out.

Points that survive go into the review with their `file:line`.

---

## Step 8: Deliver the review

Use **Conventional Comments** labels throughout to make intent unambiguous (full reference in the Comment format section below). Each observation should be prefixed with the appropriate label, e.g. `issue (blocking):`, `suggestion (non-blocking):`, `nitpick:`.

Present the review in this structure:

---

### PR #N — [Title]

**Author:** [name] | **Branch:** `[head]` → `[base]` | **Size:** +[additions] / -[deletions] across [N] files
**Coverage:** [N]/[N] files reviewed _(list any skipped file with its reason)_
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
4. **Tests** — Are there tests? If a story was fetched and has acceptance criteria, read the test diff and check each AC: is there a test that would catch a regression against it? Flag any AC with no corresponding test coverage as `issue (blocking):` — an untested AC is an unverified delivery. Beyond AC coverage: read a sample of the test diff itself — tests should assert observable behaviour, not internal implementation state. Do they cover the edge cases the diff actually touches?
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

If a PR template (`.github/PULL_REQUEST_TEMPLATE.md`) exists in the repo, check whether the PR description addresses each checklist item in substance — prose that covers the test plan or checklist counts even without the template's headings:

- **Unanswered / skipped** — flag as `question (non-blocking):` and ask the author to confirm intentionality
- **Clearly violated** (e.g. checklist says "tests required" and there are none) — flag as `issue (blocking):`

---

#### Suggested questions for the author

2–4 open questions to ask the PR author — things that are unclear from the diff alone or that could affect the review decision.

For any non-blocking point worth acting on, ask the author whether they'd rather file a follow-up story or fold the fix into this PR (which means another review round). Otherwise a non-blocking comment on an approved PR disappears when it merges.

---

## Step 9: Clean up the worktree

Remove each subagent worktree from Step 6 as soon as its findings are in. Remove the review worktree once the review is finished — after it is posted, or after the user decides not to post it. Posting waits for the user's approval, and the draft may need re-checking against the code until then:

```bash
git worktree remove --force /tmp/pr-review-<repo>-<number>
git worktree remove --force /tmp/pr-review-<repo>-<number>-code
git worktree remove --force /tmp/pr-review-<repo>-<number>-story
```

If removal fails, note it briefly to the user but do not block.

---

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
