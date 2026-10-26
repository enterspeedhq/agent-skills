# feature/pr-review-anchored-findings — 2026-10-05

## Changed files

.claude-plugin/marketplace.json
plugins/enterspeed/skills/pr-review/SKILL.md

## Observations

`pr-review/SKILL.md` Step 7.1 greps for the first line of the quote, which for a generic line (`}`, `return null;`) matches in many places and can return the wrong line number. Worth asking for the most distinctive line instead?

`pr-review/SKILL.md` Step 3 makes a clear violation of `.github/review-rules.md` an `issue` rather than a `suggestion`, while CONTRIBUTING asks skills to support judgment rather than enforce rules. Intended that the rules file sets the label, or should that stay with the reviewer?
