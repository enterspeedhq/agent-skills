# feat/shortcut-product-teams — 2026-11-23

## Changed files

- `.claude-plugin/marketplace.json`
- `plugins/enterspeed/skills/shortcut-publisher/SKILL.md`
- `plugins/enterspeed/skills/shortcut-summarizer/SKILL.md`

## Observations

Self-check after the first review round: the publisher table names the repos that decide Graph against Platform (both products have ingest, processing, delivery, management and MCP services, so the repo decides, not the service name), and says how to treat the two teams that list_teams returns besides the five boards (Agentic Product Cloud only under its epics or when named; Hamster never unless asked).

Every story is created on the Product Development workflow, Customer Success included; that team's own Customer Success workflow is for non-engineering tasks.

shortcut-summarizer: a team overview no longer filters on Engineering (which now holds only internal work) and no longer links the old Engineering Space; it spans every team and groups by team unless one is named. Its MCP tool names (iterations-get-active, stories-search) predate the current Shortcut MCP; left as they are, out of scope here.
