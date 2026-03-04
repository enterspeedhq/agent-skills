# agent-skills

Shared AI agent skills and plugins for the Enterspeed team, distributed as a Claude Code marketplace.

## Setup (one-time)

Add the following to your `~/.claude/settings.json` to register the marketplace:

```json
{
  "extraKnownMarketplaces": {
    "enterspeed": {
      "source": { "source": "github", "repo": "enterspeedhq/agent-skills" }
    }
  }
}
```

Then install the plugin:

```
/plugin install enterspeed@enterspeed
```

## Updates

Skills are added via pull requests. When a new skill is merged, the plugin version is bumped and Claude Code will auto-update at next startup — no action needed.

To manually trigger an update:

```
/plugin update enterspeed@enterspeed
```

## Contributing

1. Branch from `main`
2. Add your skill under `plugins/enterspeed/skills/<skill-name>/SKILL.md`
3. Bump the version in `plugins/enterspeed/.claude-plugin/plugin.json`
4. Open a PR with a description of what the skill does

## Structure

```
agent-skills/
├── .claude-plugin/
│   └── marketplace.json         # Marketplace definition
└── plugins/
    └── enterspeed/
        ├── .claude-plugin/
        │   └── plugin.json      # Plugin metadata + version
        └── skills/
            └── <skill-name>/
                └── SKILL.md
```
