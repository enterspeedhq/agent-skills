# Architecture Review Skill - Implementation Intent

## Core Philosophy

**Goal: Build capable teams, not enforce compliance**

This skill reduces friction by making architectural patterns discoverable, not by dictating solutions. It facilitates learning through productive struggle, not by removing all obstacles.

## Key Principles

### 1. Facilitation Over Teaching

People learn architecture through experiencing trade-offs, not hearing explanations. The skill surfaces patterns and asks questions, it doesn't prescribe answers.

### 2. Friction as Signal

Not all friction is bad. Team experiencing confusion or repeated debates signals patterns worth documenting. The skill helps make friction visible so teams can address it appropriately.

### 3. Evolutionary Discovery

Patterns emerge from real work, not upfront planning. Teams discover what matters through usage, then choose appropriate tools (guidelines, automation, or nothing) based on experienced friction.

### 4. Judgment Cannot Be Automated

Governance (rules, compliance, patterns) can and should be automated (ESLint, TypeScript). Human judgment (context, trade-offs, "does this fit?") cannot. The skill develops judgment, not just compliance.

### 5. Teams Own Patterns

Guidelines are supportive documentation of team decisions, not dictatorial mandates. Teams can challenge, update, or remove guidelines based on real experience. Wrong guidelines get fixed immediately.

## What This Skill Does

**Surfaces patterns for evaluation:**

- "This pattern appeared 10 times in feedback"
- "This differs from documented approach"
- "Here's the rationale we documented"

**Asks questions that provoke thinking:**

- "Have you considered immutability trade-offs here?"
- "Does this context warrant different approach?"
- "What pattern makes sense given your constraints?"

**Provides context, not prescriptions:**

- Examples of the pattern (good and bad)
- Documented rationale (why this matters)
- Trade-offs to consider (not which to choose)

## What This Skill Does Not Do

**Does not dictate solutions:**

- Not: "Use pattern X"
- But: "Pattern X prioritizes Y. Does that fit your context?"

**Does not block or enforce:**

- Not: "Fix this before proceeding"
- But: "Consider this friction point, discuss with team"

**Does not replace human judgment:**

- Not: "This is wrong"
- But: "This differs from pattern. Intentional?"

## The Workflow

### For Developers

1. Make changes on feature branch
2. Self-review: Invoke skill to check against patterns
3. Evaluate feedback: Does it apply to my context?
4. Iterate: Fix clear issues, document deviations
5. Commit when satisfied (not when skill says "perfect")

**Learning happens in step 3 - evaluating applicability.**

### For Autonomous Agents

1. Implement feature (AI-generated code)
2. Self-review: Run skill on changes
3. Evaluate: Does feedback indicate real issue?
4. Fix or justify: Apply judgment, iterate
5. Escalate if stuck after 3 attempts

**Agent learns what patterns matter through iteration.**

### For Teams

1. Work surfaces friction (debates, confusion, repeated issues)
2. Agent analyzes: "Pattern X appeared in 12 PRs"
3. Team discusses: Is this worth addressing? How?
4. Team chooses tool: Guideline? ESLint rule? Nothing?
5. Implement and iterate based on continued experience

**Team discovers and owns their patterns.**

## Strategy Selection (Automatic)

Skill adapts review depth to change size:

- **Small (<15 files):** Full detailed review
- **Medium (15-50 files):** Summary + critical files
- **Large (50+ files):** Suggest splitting + high-level scan

This happens automatically based on complexity calculation.

## Pattern Evolution

### Guidelines Emerge from Usage

Not written upfront. Written when friction becomes clear through real work.

### Automation Follows Understanding

ESLint rules created after pattern appears consistently and team agrees it reduces friction.

### Agent Helps Discovery

Periodically: "Analyze last 20 PRs for recurring patterns"
Agent surfaces data → Team discusses → Team decides action

### Continuous Refinement

Guidelines updated immediately when wrong. No ceremony, no approval process. Living documents.

## Trade-offs Accepted

**Trading perfection for pragmatism:**

- 75% consistency (vs 95% with strict governance)
- 15-second review time (vs instant static analysis)
- ~$10/month API costs (vs free tooling)

**Getting practical value:**

- Fast implementation (days not weeks)
- Evolutionary approach (discover what matters)
- Educational feedback (builds understanding)
- Team autonomy (reduces bottlenecks)
- Scales through capability (not just automation)

## Governance vs Facilitation

**Governance (automate this):**

- Rule compliance checking
- Pattern validation
- Syntax correctness
- Mechanical enforcement

**Facilitation (skill does this):**

- Pattern recognition development
- Trade-off evaluation
- Contextual judgment
- Architectural thinking

**All governance can be automated. Human judgment cannot.**

The skill builds judgment by preserving productive struggle while removing clarity obstacles.

## What Good Looks Like

### Team behaviors indicating success:

- Referencing guidelines naturally in discussions
- Fewer "which pattern?" questions over time
- Self-correction before review
- Challenging guidelines when they don't fit
- Teaching patterns to others through rationale, not rules

### Red flags indicating course correction needed:

- Team ignoring skill feedback
- High false positive rate (skill flags correct code)
- Guidelines creating more debate than resolution
- Feeling like enforcement theater
- Team waiting for "just tell me what to do"

## Implementation Approach

**Start minimal:**

1. One guideline document (what matters most)
2. Basic SKILL.md with strategy selection
3. Test on real PRs
4. Iterate based on what you learn

**Expand based on friction:**

- Team debates X repeatedly → Document X
- Pattern appears consistently → Consider automation
- Guideline confuses → Add examples from confusion

**No timeline. No schedule. Respond to experienced friction.**

## In AI-Assisted Development

**AI generates code fast. Humans evaluate quality.**

The skill shifts from teaching implementation to teaching evaluation:

- Is this AI-generated pattern correct?
- Does it fit our architectural principles?
- What edge cases might AI have missed?
- Should we accept, modify, or reject?

**Learning moved up a level:** From "how to implement" to "how to judge implementation."

## Why This Matters Long-term

**Building people, not just systems:**

Strong governance produces compliant code but dependent teams.
This approach produces capable teams who can evolve systems without constant oversight.

**Scaling through capability:**

As the organization grows, teams replicate the process of friction discovery, pattern emergence, and tool selection. The approach becomes culture, not just process.

**Future-proof:**

Governance gets automated by AI. Judgment development remains human work. This skill focuses on the part that won't be automated away.

---

Start imperfect. Improve based on real usage. Let patterns emerge rather than planning them all upfront.
