# Claude guidance for this repo

## What this repo is

A Claude Code skill marketplace for the Enterspeed team. Skills are markdown files — no code to run, no build step, no tests. The "output" is the quality and clarity of the skill instructions themselves.

## How to work here

- When adding or modifying a skill, read `CONTRIBUTING.md` first — it defines what good looks like
- Run **pre-flight** before raising a PR: `claude "pre-flight"`
- Bump the version in `.claude-plugin/marketplace.json` with every skill change

## Skill writing conventions

- Skills surface questions, not verdicts — never tell the user what to do, ask whether something is intentional
- Every step that can fail must say explicitly: stop, ask, or continue with a fallback
- If a step feels like a detour from the skill's stated job, it doesn't belong in the skill
- Trigger descriptions are written for Claude to parse, not for humans to read — be specific and include exact phrases

## What not to do

- Do not add a `version` field to skill frontmatter — skills are versioned via git, not frontmatter
- Do not overwrite existing docs without reading them first
- Do not open PRs or push commits unless explicitly asked or the active skill instructs it
- Do not add enforcement or blocking behaviour to skills — that belongs in CI
