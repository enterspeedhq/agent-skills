# feat/shortcut-product-teams — 2026-11-23

## Changed files

- `.claude-plugin/marketplace.json`
- `plugins/enterspeed/skills/shortcut-publisher/SKILL.md`

## Observations

Self-check: the team table matches the five teams in the workspace (Graph, Platform, Speedtrain, Customer Success, Engineering), and the step asks the user when no team clearly fits instead of falling back to Engineering, per the repo's ask-don't-decide convention.

The step stops when the chosen team does not exist, so a renamed team fails loudly rather than landing the story on the wrong board. shortcut-summarizer still describes Engineering as the team overview; left as it is, since it only filters reads.
