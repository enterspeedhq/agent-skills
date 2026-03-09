# add-pre-flight-skill — 2026-03-09

## Changed files
.github/workflows/skill-review.yml
CONTRIBUTING.md
docs/pre-flight-design.md
plugins/enterspeed/skills/pr-review/SKILL.md
plugins/enterspeed/skills/pre-flight/SKILL.md

## Observations
`plugins/enterspeed/skills/pr-review/SKILL.md` — the inserted Step 3 pushed the original Step 4 (checkout) and everything after it out of sequence. There are now two Step 4s. Anything driving that, or worth renumbering?

`CONTRIBUTING.md` line 9 — `claude "pre-flight"` assumes the enterspeed plugin is installed. A developer who hasn't set it up won't know why this fails. Worth a pointer to setup, or intentional?
