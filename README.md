# agent-skills

Shared AI agent skills for the Enterspeed team, distributed as a Claude Code marketplace.

## Setup (one-time)

From your terminal, run:

```bash
claude plugin install enterspeed@enterspeed --scope project
```

> **Note:** Once org-managed settings are fully configured, this step will happen automatically for all team members. Until then, each person runs the command above once.

## Updates

Skills are added via pull requests. When a new skill is merged, the plugin version is bumped and Claude Code will auto-update at next startup — no action needed.

To manually trigger an update:

```bash
claude plugin update enterspeed@enterspeed
```

## Contributing

1. Branch from `main`
2. Add your skill under `plugins/enterspeed/skills/<skill-name>/SKILL.md`
3. Bump the version in `.claude-plugin/marketplace.json`
4. Open a PR — the template will guide you

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
