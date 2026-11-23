---
name: shortcut-summarizer
description: Fetch and summarize Shortcut stories for a given owner, time range, and workflow column. Use this skill whenever the user asks to "show my completed stories", "what did I work on", "list stories in doing", "show last 2 weeks", "what has [person] done", "summarize my sprint", "what's in development", "what's ready for review", "give me an overview of the team", or any request to retrieve and display Shortcut stories. Defaults to the token owner, last 4 weeks, and done column — all overridable via natural language. Also used as a data-fetching step by other skills like shortcut-demo-planner.
---

# Shortcut Summarizer

Fetches Shortcut stories matching flexible criteria and presents a clean summary using the Shortcut MCP tools.

---

## Step 1: Parse Intent

Extract from the conversation:

| Parameter   | Default   | Natural language overrides                                                   |
|-------------|-----------|------------------------------------------------------------------------------|
| `weeks`     | `4`       | "last 2 weeks" → 2, "last sprint" → 2, "last week" → 1                     |
| `state`     | `done`    | "in development", "ready for review", "blocked", "ready for deploy" → match by name |
| `owner`     | `me`      | "for Sarah" → name, "whole team" / "everyone" / "the team" → all owners     |
| `group`     | *(none)*  | "graph team" / "platform board" / "speedtrain" / "customer success" / "engineering team" → that team |
| `iteration` | *(none)*  | "current iteration" / "kanban" → `Continues Kanban`                        |

### Enterspeed teams

Each product has its own team: `Graph`, `Platform`, `Speedtrain` and `Customer Success`. `Engineering` holds internal work and PoCs only, so it is not the whole team's work.

When the user asks about **the team's work** without naming a product (e.g. "what's in development", "team overview", "what's the team working on"), use these defaults:

- owner: team (all members)
- group: *(none)*, so every team is included; group the summary by team
- iteration: `Continues Kanban`

When the user names a product or team, set `group` to that team.

---

## Step 2: Fetch Stories via MCP

Before running: if the Shortcut MCP tools are not available, guide the user to run the **shortcut-setup** skill first.

Use the Shortcut MCP tools — no scripts or API tokens needed.

### Find the active iteration (if filtering by iteration)

Call `iterations-get-active` to get the current iteration, or `iterations-search` to find one by name.

### Fetch stories by iteration

If an iteration is known, use `iterations-get-stories` with the iteration ID, then filter results by state name client-side.

### Fetch stories by search query

Use `stories-search` for owner/state/date-based queries:

- `owner:me` — stories assigned to the authenticated user
- `owner:"Viktor"` — stories assigned to a specific person
- `state:"in development"` — filter by workflow state name
- `team:"Graph"` — filter by team (use the team's name)
- `updated:>YYYY-MM-DD` — compute the cutoff date from the `weeks` parameter

For team overviews, omit `owner:`; add `team:` only when a team is named.

For detailed story content (descriptions, PRs), call `stories-get-by-id` on individual stories as needed.

---

## Step 3: Present the Summary

- Header: "Found N stories — [owner], [group if set], [iteration if set], state: [state]"
- For an overview across teams, group by team first
- Group by epic if stories share an epic, otherwise flat list
- One line per story: `#ID — Story name (type) | Owner`
- If no stories found, say so clearly and suggest widening the time range, checking the state name, or verifying the group/iteration filters

Keep it scannable.

**When called as a dependency by another skill** (e.g. shortcut-demo-planner), return the story data for that skill to process — skip the formatted chat summary.
