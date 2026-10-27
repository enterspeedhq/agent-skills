# Document mode

A decision document is reviewed for whether it records the direction that was agreed, not for correctness of code. These overrides apply when Step 2 picked document mode; every other step runs as written.

**Where the repo's rules come from.** The repo defines what its ADRs and RFCs are: genre, status lifecycle, supersession format, where they live. Read them in Step 3 from `CLAUDE.md` / `AGENTS.md` / the ADR folder's README. Apply those, not general habits.

**Step 4 (worktree):** still create it — the corpus must be read at the PR head. Skip building and running tests.

**Step 6 (analysis):** read every changed document in full. Then read around it:

- **Where the direction was settled.** Find the RFC, its PR discussion, or the decision story the document ratifies or departs from. That is the standard, not the document under review: if they disagree, the ratifying document is the one that is wrong.
- **The corpus in the area.** List the existing ADRs and RFCs on the same subject with their status. Check that supersession links resolve in both directions, and that the number isn't already taken on `origin/<default>` or another open branch.
- **Claims about today's code.** Check each one at `origin/<default>` with `git grep` or `git show`, never a working tree, and cite `file:line`.

The two subagents' briefs change accordingly, each in its own worktree on the review commit (`/tmp/pr-review-<repo>-<number>-direction` and `-corpus`, created as in Step 6): one checks the document against where the direction was settled; the other checks it against the corpus and the code it makes claims about. Describe any disagreement neutrally ("do X and Y agree, and which is right?").

**Step 8 (briefing):**

- **What it achieves** becomes **what it decides** (ADR) or **what it argues** (RFC), in two plain lines.
- **How it works** becomes **what changes**: the before → after of the decision, with a short example in the syntax or wire format concerned when that makes it concrete.
- **Tests** is replaced by the **decision check**, three questions:
  1. Is every reversal on the record? A note saying "unchanged" where something actually reversed is a finding; the fix is to say a change happened, not to prescribe what replaces what. Being on the record isn't the end of it: for a recorded reversal or departure, brief the trade itself and whether its premises hold (e.g. "no external consumers yet, so a lockstep rename is cheapest now": is that still true?), so the reviewer can ask "why not all the way?".
  2. Is an open decision being closed by implication, with nothing recorded?
  3. Is something the RFC left open written down as settled?
  Also state the genre and status: is this argument (RFC) or agreement (ADR), and does the status match what merging it means in this repo?
- **What needs you** separates *product* decisions (scope, billing, customer-facing behaviour) from *technical* ones. In document mode most findings are questions for the team, not fixes: name the decision and the constraints it must satisfy, and leave the answer to the authors.
- Hygiene (formatting, links, dates, numbering style) goes in one line at the end of the draft, if at all.

