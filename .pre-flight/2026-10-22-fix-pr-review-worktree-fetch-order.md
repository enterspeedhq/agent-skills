# fix/pr-review-worktree-fetch-order — 2026-10-22

## Changed files

.claude-plugin/marketplace.json
plugins/enterspeed/skills/pr-review/SKILL.md

## Observations

`pr-review/SKILL.md` Step 8 now ties cleanup to posting, but posting happens in **pr-submit-review**, not this skill. Clear enough as "once the review is finished", or worth naming the sibling skill?
