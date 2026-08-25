---
name: shortcut-setup
description: Set up the Shortcut MCP server for use with Shortcut skills. Use this skill whenever the user gets a Shortcut MCP tool error, asks "how do I set up Shortcut", is running a Shortcut skill for the first time, or wants to migrate off the deprecated self-hosted Shortcut MCP server. Referenced by shortcut-publisher and shortcut-summarizer.
---

# Shortcut Setup

One-time setup to connect Claude to Shortcut via the **official hosted MCP server** (`https://mcp.shortcut.com/mcp`). Authentication is OAuth — no API token to create, store, or rotate. Once done, all Shortcut skills work without further configuration.

> The old self-hosted server (`npx @shortcut/mcp`) is **deprecated** — it warns on every tool call and is no longer maintained. Step 1 removes it if present.

---

## When to use this skill

Guide the user through this setup if:
- A Shortcut skill fails with a tool-not-found or MCP error
- Shortcut tool calls return a deprecation warning
- The user asks how to connect to Shortcut
- This is their first time using a Shortcut skill

---

## Setup steps

### 1. Remove the deprecated self-hosted server if present

First confirm the CLI is available:

```bash
claude --version
```

If that fails, `claude` is not on PATH — stop and tell the user to run these steps from a terminal where the Claude Code CLI is installed, or to configure the server through claude.ai's connector settings instead (step 2, second path).

Then list the configured servers:

```bash
claude mcp list
```

If a `shortcut` entry running `npx @shortcut/mcp` appears, remove it:

```bash
claude mcp remove shortcut --scope user
```

**The entry can exist in more than one scope** (user `~/.claude.json`, project `.mcp.json`, local). If `claude mcp list` still shows it after removal, repeat with `--scope project` and `--scope local` until it is gone — a copy in a missed scope silently keeps loading everywhere.

If a removal command fails, do not continue past it — report which scope failed and why. The usual cause is the project scope: `--scope project` rewrites the repository's `.mcp.json`, which is a **shared, committed file**, so the removal shows up as a working-tree change that must be committed and pushed for the rest of the team to be rid of the entry. If that file is read-only, owned by another team, or the user cannot land a change to it, stop and tell them the project-scope entry needs an owner to remove it — leaving it in place keeps the deprecated server loading for everyone in that repo.

The old server used a `SHORTCUT_API_TOKEN` stored inline in config. After removing the entry, tell the user to **revoke that token** at `https://app.shortcut.com/enterspeed/settings/account/api-tokens` — the hosted server does not use it, and inline plaintext tokens violate Enterspeed's security policy.

If no self-hosted entry appears, continue to step 2.

### 2. Add the hosted server

```bash
claude mcp add --transport http shortcut https://mcp.shortcut.com/mcp --scope user
```

Alternatively, on a Claude Teams account the Shortcut connector can be enabled in claude.ai's connector settings — it then appears in Claude Code automatically as `claude.ai Shortcut`. Either path works; do not set up both.

### 3. Authenticate

In an **interactive** Claude Code session, run `/mcp`, select the `shortcut` server, and complete the OAuth flow in the browser.

On the claude.ai connector path the entry is named `claude.ai Shortcut` rather than `shortcut` — same flow, different label, so select that one instead. Nothing has been missed.

If the current session is non-interactive (headless, cron, CI), stop and tell the user authentication must be completed once in an interactive session first.

### 4. Restart and verify

MCP servers are loaded at session start — start a fresh session, then verify by asking Claude to list recent Shortcut stories. If the tools are still missing, run `claude mcp list` and check the `shortcut` entry (or `claude.ai Shortcut` on the connector path) shows `✓ Connected`; a `Needs authentication` status means step 3 was not completed.

---

## After setup

The Shortcut MCP tools are available automatically in all future sessions, with authentication handled by OAuth — no token maintenance required.
