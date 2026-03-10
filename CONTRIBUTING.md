# Contributing

## Skill design philosophy

Skills in this repo are designed to support judgment, not enforce compliance. That means:

- Surface observations as questions, not verdicts — the developer decides
- Check for pattern deviations and contextual fit, not just rule violations
- Never block or gate — a skill that stops work to enforce a rule belongs in CI, not here
- One skill, one job — if a step feels like a detour, it belongs elsewhere

This shapes everything below. If a quality issue you're adding to a skill doesn't fit this framing, it probably belongs in a lint rule or CI check instead.

---

## Adding or updating skills

### Before raising a PR

Run pre-flight on your branch:

```bash
claude "pre-flight"
```

This requires the enterspeed plugin to be installed. If the skill isn't recognized, follow the setup instructions in the [README](README.md).

Review the log written to `.pre-flight/` and edit out anything you don't want to share before committing it alongside your changes.

### Skill structure

Each skill lives in `plugins/enterspeed/skills/<skill-name>/SKILL.md`. The folder may also contain `scripts/`, templates, or other resources the skill needs. See [README — Skill file structure](README.md#skill-file-structure) for the full reference.

For the official skill specification, see [Anthropic's skill documentation](https://docs.anthropic.com/en/docs/agents/skills).

**Frontmatter** — two fields required:

```yaml
---
name: skill-name
description: When to trigger this skill. Include concrete trigger phrases.
---
```

**Description** — written for Claude, not humans. It must be specific enough for Claude to know exactly when to invoke the skill. Include the phrases a user would naturally say. Vague descriptions cause missed or false triggers.

**Body** — sequential steps, each doing one thing. Give Claude enough context to act without ambiguity. If a step has an error condition, say explicitly what to do (stop, ask, continue).

**Scope** — one skill, one job. If a skill is trying to do two unrelated things, split it.

### Common quality issues to watch for

**Scope creep** — the skill starts doing a second unrelated thing partway through. Each step should serve the same job. If a step feels like a detour, it probably belongs in a separate skill or shouldn't exist.

**Vague trigger description** — descriptions like "use when the user wants help with X" are too broad. Claude needs to know the exact phrases or situations. If you can't write three concrete trigger phrases, the skill's scope isn't clear yet.

**Ambiguous error handling** — every step that can fail should say explicitly what to do: stop and tell the user, ask a question, or continue with a fallback. "Handle errors appropriately" is not enough — Claude will guess, and guesses diverge.

**Missing stop conditions** — if the skill should exit early (nothing to do, prerequisite not met, user cancels), say "stop" explicitly. Without it, Claude may continue into steps that assume prior steps succeeded.

**Implicit assumptions** — steps that assume the user has a tool installed, a branch checked out, or a file present without checking first. Verify before acting, or state the prerequisite clearly.

**Over-specified output** — prescribing exact wording for every message makes the skill brittle and robotic. Specify structure and intent; leave phrasing to Claude unless the exact wording matters.

### How guidelines evolve

Guidelines here are written from observed friction, not theory. If the team debates the same question repeatedly, document the trade-off. If a quality issue appears consistently in pre-flight logs, consider formalizing it. If a guideline confuses more than it helps, fix or remove it — no approval process needed.

### Companion scripts

Place helper scripts in `<skill-name>/scripts/<file>`. Reference them in the skill body as `<skill-path>/scripts/<file>` where `<skill-path>` is the directory containing `SKILL.md`.

### Referencing other skills

Reference sibling skills by name in bold: **skill-name**. Claude resolves these by name — no import mechanism needed.

### Plugin version

Bump the version in `.claude-plugin/marketplace.json` when shipping any skill change. The CI will remind you if you forget.

## References

- [Anthropic's skill documentation](https://docs.anthropic.com/en/docs/agents/skills) — official skill specification
- [Standard Readme](https://github.com/RichardLitt/standard-readme) — README structure and conventions
- [GitHub contributing guidelines](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors) — contribution docs best practices
- [Architecture Decision Records](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — ADR format and rationale
