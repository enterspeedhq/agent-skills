---
name: shortcut-summarizer
description: >
  Fetch and summarize Shortcut stories for a given owner, time range, and
  workflow column. Use this skill whenever the user asks to "show my completed
  stories", "what did I work on", "list stories in doing", "show last 2 weeks",
  "what has [person] done", "summarize my sprint", "what's in development",
  "what's ready for review", "give me an overview of the team", or any request
  to retrieve and display Shortcut stories. Defaults to the token owner, last 4
  weeks, and done column — all overridable via natural language. Also used as a
  data-fetching step by other skills like shortcut-demo-planner.
---

# Shortcut Summarizer

Fetches Shortcut stories matching flexible criteria and presents a clean summary.

---

## Step 1: Parse Intent

Extract from the conversation:

| Parameter   | Default     | Natural language overrides                                                   |
|-------------|-------------|------------------------------------------------------------------------------|
| `weeks`     | `4`         | "last 2 weeks" → 2, "last sprint" → 2, "last week" → 1                     |
| `state`     | `done`      | "in development", "ready for review", "blocked", "ready for deploy" → match by name |
| `owner`     | `me`        | "for Sarah" → name, "whole team" / "everyone" / "the team" → `team`         |
| `group`        | *(none)*    | "engineering team" / "engineering space" → `Engineering`                  |
| `iteration`    | *(none)*    | "current iteration" / "kanban" → `Continues Kanban`                      |
| `with-details` | `false`     | "include PRs", "show descriptions", "with context" → add `--with-details` |

### Enterspeed Engineering Space

When the user asks about the **Engineering team's work** (e.g. "what's in development", "engineering team overview", "what's the team working on"), use these defaults:

```
--owner team --group Engineering --iteration "Continues Kanban"
```

This matches the Engineering space in the Shortcut UI at:
`https://app.shortcut.com/enterspeed/stories/space/4297`

---

## Step 2: Run the Fetch Script

The fetch script lives at `scripts/fetch_stories.py`. Copy it to a writable
location (note: `/tmp` may not be writable in all environments — use a path
under `/sessions/<session>/` instead) and run it:

```bash
cp <skill-path>/scripts/fetch_stories.py /sessions/<session>/fetch_stories.py

SHORTCUT_API_TOKEN="..." python3 /sessions/<session>/fetch_stories.py \
  --weeks <N> \
  --state <state> \
  --owner <me|team|name> \
  [--group <group name>] \
  [--iteration <iteration name>] \
  > /sessions/<session>/shortcut_stories.json
```

Examples:
```bash
# Engineering team, current kanban, in development
python3 fetch_stories.py --owner team --group Engineering --iteration "Continues Kanban" --state "in development"

# Engineering team, ready for review — with full descriptions and PRs
python3 fetch_stories.py --owner team --group Engineering --iteration "Continues Kanban" --state "ready for review" --with-details

# My completed stories, last 2 weeks
python3 fetch_stories.py --weeks 2 --state done

# Another team member's in-progress work
python3 fetch_stories.py --owner "Viktor" --state "in development"

# Whole team, no group/iteration filter
python3 fetch_stories.py --owner team --state "ready for deploy"
```

The script reads `SHORTCUT_API_TOKEN` from the environment. If it is not set,
follow the **shortcut-setup** skill for step-by-step instructions on securely
storing and auto-loading the token via 1Password.

---

## Step 3: Present the Summary

Read the output JSON and display in chat:

- Header: "Found N stories — [owner], [group if set], [iteration if set], state: [state]"
- Group by epic if `epic_id` is present, otherwise flat list
- One line per story: `#ID — Story name (type) | Owner`
- If no stories found, say so clearly and suggest widening the time range, checking the state name, or verifying the group/iteration filters

Keep it scannable. Descriptions are preserved in the JSON for downstream skills.
When the user asks for a detailed summary of each story, fetch full story details
via `GET /stories/{id}` for any stories that have an empty description in the JSON.

---

## Script reference

See `scripts/fetch_stories.py` for the full implementation. It uses only the
Python standard library and the Shortcut REST API — no extra dependencies.

Supported flags:
- `--weeks N` — look back N weeks (default: 4)
- `--state STATE` — workflow state name fragment or "done" (default: "done")
- `--owner me|team|NAME` — filter by owner (default: "me")
- `--group NAME` — filter by Shortcut group/team name (e.g. "Engineering")
- `--iteration NAME` — filter by iteration name (e.g. "Continues Kanban")
- `--with-details` — fetch full story details per story (description + PRs); omit for fast bulk results
