# feature/app-platform-poc-otel — 2026-11-27

## Changed files

.claude-plugin/marketplace.json
plugins/enterspeed/skills/app-platform-poc/SKILL.md
plugins/enterspeed/skills/app-platform-poc/references/app-platform-blueprint.md

## Observations

1. `app-platform-poc/SKILL.md` describes the blueprint as a verbatim copy of the team document, and this change edits the copy in §1, §6.1, §6.3, §8, §10.1 and §11. Is the team document being updated to match, or should this land there first?
2. The version goes to 1.25.0, which the open `feature/poc-provision-skill` branch also uses. Fine to bump whichever merges second, or worth agreeing the order now?
3. Telemetry is added to the platform only; the React app gets no browser telemetry. Intentional for PoCs, or worth a follow-up?
