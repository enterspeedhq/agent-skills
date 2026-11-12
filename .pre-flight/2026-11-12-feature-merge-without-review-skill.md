# feature/merge-without-review-skill — 2026-11-12

## Changed files

.claude-plugin/marketplace.json
plugins/enterspeed/skills/merge-without-review/SKILL.md

## Observations

1. The policy table and template (SKILL.md:21–36) repeat the Development Process doc in Shortcut, and the skill says the doc wins but has no way to notice when they diverge. Is keeping a copy in the skill intentional (so it works without Shortcut), or should it fetch the doc section at runtime?
2. Step 1 carries on for any open PR that isn't `APPROVED`, including PRs in `baseline` repos where no review is required and `reviewDecision` is empty, so the skill would admin-merge where a normal merge works. Should it tell the user there's nothing to bypass there?
3. The planned high-risk row lets the engineer bypass after one nudge, where the Development Process doc says to request a review. Is the softer wording intentional (skills don't block), or should the doc be aligned?
