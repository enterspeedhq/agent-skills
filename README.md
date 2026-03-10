# agent-skills

Shared AI agent skills for the Enterspeed team, distributed as a Claude Code marketplace.

## Setup (one-time)

From your terminal, run:

```bash
claude plugin marketplace add https://github.com/enterspeedhq/agent-skills
claude plugin install enterspeed@enterspeed
```

> **Note:** Once org-managed settings are fully configured, this step will happen automatically for all team members. Until then, each person runs the commands above once.

## Updates

Skills are added via pull requests. When a new skill is merged, the plugin version is bumped and Claude Code will auto-update at next startup — no action needed.

To manually trigger an update:

```bash
claude plugin marketplace update enterspeed
claude plugin update enterspeed@enterspeed
```

> **Note:** The marketplace name is `enterspeed` (not the full GitHub URL). Run both commands — the first refreshes the index from GitHub, the second installs the latest version.

## Contributing

### Skill file structure

Every skill has a `SKILL.md` file and may include additional resources:

```
plugins/enterspeed/skills/<skill-name>/
├── SKILL.md                    # Required: skill definition
├── scripts/                    # Optional: helper scripts
│   └── <script-file>
├── templates/                  # Optional: templates or config files
└── <other-resources>           # Optional: test data, fixtures, etc.
```

The `SKILL.md` must start with:

```yaml
---
name: your-skill-name
description: When to trigger this skill — be specific, this is what Claude reads to decide whether to use it.
---
```

Followed by the skill body: instructions, context, templates, or anything Claude should know when the skill activates.

### Steps

1. Branch from `main`
2. Create `plugins/enterspeed/skills/<skill-name>/SKILL.md`
3. Bump the version in `.claude-plugin/marketplace.json` (e.g. `1.2.0` → `1.3.0`)
4. Open a PR — the template will guide you

### Tips

- The `description` field is critical — it's how Claude decides when to invoke your skill. Be explicit about trigger phrases and use cases.
- Keep skills focused on one thing. Compose multiple skills for complex workflows (see `shortcut-demo-planner` for an example).
- If your skill needs scripts, add them alongside `SKILL.md` under the same directory.

## Structure

```
agent-skills/
├── .claude-plugin/
│   └── marketplace.json         # Marketplace definition + version
└── plugins/
    └── enterspeed/
        ├── .claude-plugin/
        │   └── plugin.json      # Plugin metadata
        └── skills/
            └── <skill-name>/
                └── SKILL.md
```
