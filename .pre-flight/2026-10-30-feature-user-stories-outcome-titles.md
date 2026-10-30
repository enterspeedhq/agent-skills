# feature/user-stories-outcome-titles — 2026-10-30

## Changed files

.claude-plugin/marketplace.json
plugins/enterspeed/skills/enterspeed-user-stories/SKILL.md

## Observations

1. The new "The Title" section (SKILL.md:27–34) asks for an outcome title, but the template has no title slot and **shortcut-publisher** step 3 (shortcut-publisher/SKILL.md:14) sets the Shortcut title from the "As a … I want" line. Does the publisher need a matching change for the title rule to take effect, or is that a separate PR?
2. The frontmatter `version` was bumped from 1.0.0 to 1.1.0 (SKILL.md:3), while CLAUDE.md says skills are versioned via git, not frontmatter. Keep the bump, or leave the existing field untouched?
