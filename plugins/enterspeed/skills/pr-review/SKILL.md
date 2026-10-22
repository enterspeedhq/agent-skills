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

- If the Shortcut MCP tool is unavailable or returns an error: retry once, and have the subagents try too (they often succeed when the main session can't). If it still fails, proceed without it, but say so in one line in the briefing ("story not fetched: <error>"). The Tests section then can't map acceptance criteria to tests, and on a later round an open item may be hidden
- If the story is found: store the title, description, and acceptance criteria for use in Step 7

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

If that commit is no longer an ancestor of `HEAD` (the branch was rebased or force-pushed), that diff would pick up whatever landed on the base in between, so do the full review instead. Otherwise Steps 4–7 cover only that diff, checked against the open items. Don't re-raise points that were settled, and frame the output as "Round N". Subagent validation (Step 6) then applies only to new findings from that diff; if there are none, skip it. If you haven't reviewed it before, do the full review.

**CI state.** Run `gh pr checks <number>` and read every row. A check's name may not say everything it runs (a "Build" check can include lint), and one green check says nothing about the others. Mention any failing or pending check in the summary. The exit code is data, not an error: it is `8` while checks are pending and non-zero when one has failed.

**Pick the mode.** If every changed file is a decision document (an ADR, an RFC, or the repo's equivalent: look for `docs/adr/`, `docs/rfc/`, or what the repo guide calls one) plus at most incidental index or link edits, this is a **document review**: follow the [Document mode](#document-mode) overrides below. Otherwise it is a code review. A PR that mixes a decision document with the code implementing it is a code review, with the document mode's decision check added to the briefing.

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
- `AGENTS.md` (agent conventions; a `CLAUDE.md` may only import it with `@AGENTS.md`)

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
4. **Focus on core changes**: Skip generated files (package-lock.json, .min.js, etc.), pure formatting commits, and test fixtures unless they're central to the PR

This approach balances completeness with efficiency. For a 10-file PR with 800 lines changed, targeted reading can reduce token cost by 40-60% compared to reading the full diff.

If doing a focused review due to PR size, say so explicitly in the summary: "Large PR — review focused on [specific areas]; [what was skipped] were not examined in detail."

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

## Step 7: Brief the reviewer, then draft

Present a briefing for the reviewer **before** any finding or draft. Use this layout by default; the reviewer should not have to ask for it. See [references/briefing-example.md](references/briefing-example.md) for a worked example.

1. **What it achieves.** Two plain lines. Never a bare story or PR number; always give its title.
2. **How it works.** Before → after. Use an ASCII flow or timing diagram when behaviour changes.
3. **Where it sits.**
   - Which RFCs, ADRs or design docs it implements or departs from.
   - Which other open PRs touch the same files or are stacked with it. Name the hunks, and say whether the overlap is real or only textual. Find them with `gh pr list --state open --json number,title,files`, filtered on the changed paths. Then read the reviewer's own latest review on every overlapping PR — above all doc PRs touching the same ADR. A PR that withdraws what the reviewer approved elsewhere minutes earlier reads as textual overlap unless you do.
4. **What needs you.** A **numbered** list of decisions, each marked *product* or *technical*, with options as short code or JSON and the author's own proposal first, so the reviewer can answer in one line per item ("1 agree, 2 yes, 3 …"). Their answers go into the draft in their own words, as their view rather than a ruling. For a new external surface, have prior art from comparable platforms ready. Say plainly when there is nothing to decide. Bookkeeping (approval count, CI, re-runs) goes in one line.
5. **Tests.** Map each acceptance criterion to the test that proves it, and highlight every missing test. Weigh high-level tests most — the repo's highest-level test (an HTTP-level e2e or an integration test against the real entry point) usually translates directly to an AC, so a missing one on a behaviour change is called out even when unit tests exist. A gap you judge acceptable is still stated, with the reason. A missing test never blocks: the draft encourages adding it, and the author chooses between this PR and a follow-up, like any other non-blocking finding.
6. **The draft.**
   - Plain language and short.
   - Code blocks rather than inline code for `file:line` evidence.
   - Findings phrased as questions to the author.
   - End the briefing with a one-line **Not raised** list of what validation or judgement cut, so the reviewer sees the filtering without reading the noise.
   - Close with one line that hands every non-blocking finding to the author: file follow-up stories, or fix them in this PR (another review round). **The choice is the author's judgement**, so don't steer it: no "fix it here", no suggested destination story or epic, no "your call, but I'd…". Don't offer to file follow-ups yourself.
   - Show the full draft and wait for explicit approval before posting. It goes out in the reviewer's name.
7. **Ledger**, after posting: what was posted (with link), who was re-requested, what was filed, what was cleaned up, and what is still open. Verify each post with `gh pr view <n> --json reviews` (a permission classifier may block `gh api …/reviews`), one PR per command rather than a shell loop. If removing a worktree is blocked, put the `git worktree remove` commands in the ledger for the reviewer to run.

Terminal output by default; an artifact only on request.

**Bundles.** When several PRs are reviewed together (a stack, a cross-repo pair, or one design across ADRs):

- Answer the reviewer's framing question first, if they asked one, then give **one** briefing for the bundle: a one-row-per-PR table of what each decides or changes, one before → after for the whole, and **one** numbered "What needs you" list across all of them.
- Overlap means PRs sharing a line or a decision, not just a file.
- Post **one formal review per PR**. Shared hygiene goes once, on the first PR.
- Subagents: in code mode, two per story (`-code`, `-story`); in document mode, one per PR doing both the direction and the corpus pass.

**Before ranking a subagent's finding, check the strongest one yourself** against the source (`git grep` / `git show` at a ref). Agents overrate: one ranked an ADR override first that the ADR had already anticipated. Check findings against what the reviewer has already decided (their memory, earlier reviews): a deliberate org rule is not a finding. A repo-wide code-vs-docs gap goes under "What needs you" as its own question, and into the PR draft only where it is that PR's premise.

**What to look for while forming findings** — consider these in rough priority order, and only raise what stands out:

1. **Design** — Does the approach make sense, and does the change belong here? Look for hardcoded constants that may need to vary by environment or deployment.
2. **Functionality** — Edge cases, concurrency, user-facing behaviour.
3. **Complexity** — Over-engineering, premature generalisation, unused extensibility.
4. **Tests** — If a story was fetched and has acceptance criteria, is there a test that would catch a regression against each AC? An AC with no test is an unverified delivery. Tests should assert observable behaviour, not internal state, and cover the edge cases the diff touches.
5. **Security** — Input validation, auth checks, secrets, injection, data exposure.
6. **Breaking changes** — API contract changes, schema migrations, removed or renamed fields.
7. **Performance** — N+1 queries, missing indexes, large allocations in hot paths.
8. **Naming**, **Comments** (why, not what), **Documentation**, and **Style** against the repo's own docs.

**Checklist alignment** — if `.github/PULL_REQUEST_TEMPLATE.md` exists, check whether the PR description addresses each item in substance — prose that covers the test plan or checklist counts even without the template's headings. An unanswered item is a question to the author; a clearly violated one (e.g. "tests required" with none) is a blocking finding.

---

## Step 8: Clean up the worktree

Remove each subagent worktree from Step 6 as soon as its findings are in. Remove the review worktree after the ledger (Step 7.7) — not before, because posting waits for the reviewer's approval and the draft may need re-checking against the code:

```bash
git worktree remove --force /tmp/pr-review-<repo>-<number>
git worktree remove --force /tmp/pr-review-<repo>-<number>-code
git worktree remove --force /tmp/pr-review-<repo>-<number>-story
```

If removal fails, note it briefly to the user but do not block.

---

## Document mode

A decision document is reviewed for whether it records the direction that was agreed, not for correctness of code. These overrides apply when Step 2 picked document mode; every other step runs as written.

**Where the repo's rules come from.** The repo defines what its ADRs and RFCs are: genre, status lifecycle, supersession format, where they live. Read them in Step 3 from `CLAUDE.md` / `AGENTS.md` / the ADR folder's README. Apply those, not general habits.

**Step 4 (worktree):** still create it — the corpus must be read at the PR head. Skip building and running tests.

**Step 6 (analysis):** read every changed document in full. Then read around it:

- **Where the direction was settled.** Find the RFC, its PR discussion, or the decision story the document ratifies or departs from. That is the standard, not the document under review: if they disagree, the ratifying document is the one that is wrong.
- **The corpus in the area.** List the existing ADRs and RFCs on the same subject with their status. Check that supersession links resolve in both directions, and that the number isn't already taken on `origin/<default>` or another open branch.
- **Claims about today's code.** Check each one at `origin/<default>` with `git grep` or `git show`, never a working tree, and cite `file:line`.

The two subagents' briefs change accordingly: one checks the document against where the direction was settled; the other checks it against the corpus and the code it makes claims about. Describe any disagreement neutrally ("do X and Y agree, and which is right?").

**Step 7 (briefing):**

- **What it achieves** becomes **what it decides** (ADR) or **what it argues** (RFC), in two plain lines.
- **How it works** becomes **what changes**: the before → after of the decision, with a short example in the syntax or wire format concerned when that makes it concrete.
- **Tests** is replaced by the **decision check**, three questions:
  1. Is every reversal on the record? A note saying "unchanged" where something actually reversed is a finding; the fix is to say a change happened, not to prescribe what replaces what. Being on the record isn't the end of it: for a recorded reversal or departure, brief the trade itself and whether its premises hold (e.g. pre-prod makes a lockstep rename cheapest now), so the reviewer can ask "why not all the way?".
  2. Is an open decision being closed by implication, with nothing recorded?
  3. Is something the RFC left open written down as settled?
  Also state the genre and status: is this argument (RFC) or agreement (ADR), and does the status match what merging it means in this repo?
- **What needs you** separates *product* decisions (scope, billing, customer-facing behaviour) from *technical* ones. In document mode most findings are questions for the team, not fixes: name the decision and the constraints it must satisfy, and leave the answer to the authors.
- Hygiene (formatting, links, dates, numbering style) goes in one line at the end of the draft, if at all.

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
