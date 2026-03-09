# pre-flight — Design Rationale

## What problem this solves

Developers catching their own issues before review is cheaper than reviewers catching them. Reviewers catching architectural deviations is cheaper than post-merge corrections. This skill gives developers a consistent self-check at the cheapest point in the cycle.

## Why questions, not verdicts

Static analysis tools (ESLint, TypeScript) handle rule compliance. They're fast, free, and unambiguous — use them for that.

What they can't do is evaluate context. "Is mutable state wrong here?" depends on constraints the tool doesn't know. The pre-flight skill asks questions precisely because context matters. A developer who answers "yes, intentional, because X" has done something more valuable than fixing a lint error — they've evaluated a trade-off.

The skill checks both: pattern deviations (governance) and contextual fit (judgment). The same question serves both without labeling either.

## Why observations, not scores

A score invites gaming. "Clean" invites complacency. Neither tells the developer what to think about. A specific observation with a question — "this has four exit points, anything driving that shape?" — directs attention without removing the decision.

## Why logs get written

Observations accumulate as data. Patterns in that data reveal what teams actually struggle with, which is different from what architects think they struggle with. Guidelines written from real friction stick. Guidelines written from theory often don't.

The log is also visible to the reviewer. If no log exists, the reviewer knows the author skipped self-review — useful signal without a gate.

## Why the skill adapts to diff size

Large diffs overwhelm attention. A focused review of 15 files produces useful observations. A scan of 80 files produces noise. The skill trades coverage for signal quality: smaller changes get full attention, larger changes get the highest-value files.

## What the skill does not do

- Block or gate — it never prevents a commit or merge
- Prescribe — it never says "use pattern X"
- Replace the reviewer — it's a self-check, not a substitute for review

## Governance vs. judgment

**Governance** (rule compliance, pattern validation, syntax) — automate this with ESLint, TypeScript, CI checks. It's faster, cheaper, and more consistent than any skill.

**Judgment** (context evaluation, trade-off assessment, "does this fit here?") — the skill supports this. It can't be automated because it requires knowing things the tool doesn't know.

The skill sits entirely in the judgment column.

## How guidelines evolve

Guidelines aren't written upfront — they're written when friction becomes clear:

- Team debates the same question repeatedly → document the trade-off
- Pattern appears consistently in pre-flight logs → consider formalizing
- Guideline confuses more than it helps → fix or remove it immediately

No ceremony. No approval process. Wrong guidelines get fixed when they're discovered to be wrong.

## When to add automation

ESLint rules, commit hooks, and CI checks are appropriate after a pattern has:
1. Appeared consistently enough to be worth automating
2. Been discussed and agreed on by the team
3. Shown that the automated check reduces friction, not just enforces compliance

Automation before understanding produces enforcement theater.

## What success looks like

- Developers reference guidelines naturally without being prompted
- Pre-flight logs show fewer repeated observations over time on the same patterns
- Reviewers raise fewer architectural issues that pre-flight should have caught
- Teams update guidelines when they don't fit, rather than ignoring them

## What failure looks like

- Observations are generic (no guideline docs exist to calibrate against)
- High false positive rate (skill flags code that's actually correct)
- Developers stop running it because it adds noise without value
- Guidelines accumulate but never get updated

## In AI-assisted development

AI generates code faster than humans review it. The skill's role shifts: less about implementation quality (AI handles that reasonably well) and more about architectural fit.

The useful questions become:
- Does this AI-generated approach match how we've solved similar problems here?
- What edge cases might the AI have not considered given our specific context?
- Should we accept, modify, or push back on this pattern?

The skill is particularly valuable as a mandatory step in autonomous agent workflows, where there's no human author to exercise judgment before review.
