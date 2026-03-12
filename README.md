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

## Skills using Copilot

GitHub Copilot automatically loads Agent Skills placed in any of the standard skill folders:

*   **Project skills:**  
    `.github/skills/`, `.claude/skills/`, `.agents/skills/` [\[github.com\]](https://github.com/github/awesome-copilot/blob/main/docs/README.skills.md)

*   **Personal/global skills:**  
    `~/.copilot/skills/`, `~/.claude/skills/`, `~/.agents/skills/` [\[github.com\]](https://github.com/microsoft/vscode/issues/97030)

Place (or symlink) your `skills/` folder into one of these locations and Copilot will detect it automatically.


## Skills in Rider with Copilot

Rider supports Copilot Skills but **cannot add custom folders**.  
You must use one of the standard Copilot skill directories.

You can set this up in two ways:

### **1. Link your repository skills (recommended)**

If your skills live in a Git repo, create a symlink into one of the supported directories so changes update automatically.

**Windows**

```powershell
cmd /c mklink /D "%USERPROFILE%\.copilot\skills\my-skills" "C:\path\to\repo\skills"
```

**macOS / Linux**

```bash
ln -s "/path/to/repo/skills" ~/.copilot/skills/my-skills
```

Restart Rider and the skills will load.


### **2. Add your skills directly**

Move your skill folders into:

    ~/.copilot/skills/
    ~/.claude/skills/
    ~/.agents/skills/

## Skills in VS Code with Copilot

VS Code supports the same standard skill folders as Rider and additionally allows you to **add extra skill locations**.

### **1. Use a symlink (recommended & universal)**

Use the same symlink method as Rider to link your repo to a supported directory.

### **2. Add a repository path through VS Code settings**

1.  Open **Settings**
2.  Search for **“Agent Skills”**
3.  Open **Agent Skill Locations**
4.  Add the folder where your `skills/` directory lives

VS Code will now scan and load skills from that location. 
