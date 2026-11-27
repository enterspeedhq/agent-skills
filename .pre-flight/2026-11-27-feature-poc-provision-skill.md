# feature/poc-provision-skill — 2026-11-27

## Changed files

.claude-plugin/marketplace.json
plugins/enterspeed/skills/poc-provision/SKILL.md
plugins/enterspeed/skills/poc-provision/scripts/pim_role.py

## Observations

1. The PoC subscription ID (`fa1883c7-…`) and the DKK budget default are hardcoded in `SKILL.md` Steps 2–4. Are they stable enough to live in the skill, or likely to change (e.g. a dedicated PoC subscription later)?
2. Path B (new customer subscription, Step 3) hasn't been run yet; the skill says so, but the billing and alias steps are unverified. Fine to ship as untested, or hold until the first customer request has been through it?
3. Step 6b (eligible group membership) is a manual portal step, because the Azure CLI token lacks the Graph PIM for Groups scope. Acceptable for v0, or worth scripting with Graph PowerShell?
