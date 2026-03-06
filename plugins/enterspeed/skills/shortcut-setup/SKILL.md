---
name: shortcut-setup
description: Set up the Shortcut MCP server for use with Shortcut skills. Use this skill whenever the user gets a Shortcut MCP tool error, asks "how do I set up Shortcut", or is running a Shortcut skill for the first time. Referenced by shortcut-publisher, shortcut-summarizer, and shortcut-demo-planner.
---

# Shortcut Setup

One-time setup to configure the Shortcut MCP server. Once done, all Shortcut skills will work without any further configuration.

---

## When to use this skill

Guide the user through this setup if:
- A Shortcut skill fails with a tool-not-found or MCP error
- The user asks how to connect to Shortcut
- This is their first time using a Shortcut skill

---

## Setup steps

### 1. Get your Shortcut API token

Go to: `https://app.shortcut.com/enterspeed/settings/account/api-tokens`

Generate a new token and copy it.

---

### 2. Add the MCP server to `~/.claude/mcp.json`

Create or edit `~/.claude/mcp.json` and add:

```json
{
  "mcpServers": {
    "shortcut": {
      "command": "npx",
      "args": ["-y", "@shortcut/mcp@latest"],
      "env": {
        "SHORTCUT_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

If the file already has other MCP servers, add the `"shortcut"` entry inside the existing `"mcpServers"` object.

---

### 3. Restart Claude Code

The MCP server is loaded at startup — a restart is required to pick it up.

---

## After setup

The Shortcut MCP tools will be available automatically in all future sessions. You can verify by asking Claude to list your recent Shortcut stories.
