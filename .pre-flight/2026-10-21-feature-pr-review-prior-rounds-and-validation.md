# feature/pr-review-prior-rounds-and-validation — 2026-10-21

## Changed files

.claude-plugin/marketplace.json
plugins/enterspeed/skills/pr-review/SKILL.md

## Observations

`pr-review/SKILL.md` Step 6 now sends every PR through two subagents, each with its own worktree, including a one-file PR that the same step otherwise reads in a single diff. Is that cost intended for small PRs, or should the small/large split also apply to validation?

`pr-review/SKILL.md` Step 2 says a round N+1 review covers "only the changes since that review", but doesn't say how to find that diff. The reviews API returns each review's `commit_id`, so would `git diff <commit_id>..HEAD` be worth putting in the instruction?
