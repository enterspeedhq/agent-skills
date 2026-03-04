---
name: shortcut-demo-planner
description: >
  Plan a sprint or iteration demo using completed Shortcut stories. Use this skill
  whenever the user says "plan my demo", "prepare a demo", "make a demo from my
  stories", "what should I demo", "create a demo presentation from Shortcut", or
  any combination of Shortcut story review + demo planning. Orchestrates the
  shortcut-summarizer and revealjs-presentation skills: fetches stories, groups
  them into demo-friendly themes, suggests a demo order with talking points, and
  generates a Reveal.js presentation.
---

# Shortcut Demo Planner

Orchestrates **shortcut-summarizer** + **revealjs-presentation** to turn your
recent Shortcut stories into a structured demo plan and polished slide deck.

---

## Step 1: Fetch Stories

Follow the **shortcut-summarizer** skill to fetch stories.

Default parameters for demo planning:
- `--weeks 4`
- `--state done`
- `--owner me`

Override based on what the user says. Save output to `/tmp/shortcut_stories.json`.

---

## Step 2: Build the Demo Plan

Read `/tmp/shortcut_stories.json` and produce a demo plan in chat before generating slides. Structure it as:

### Grouping logic (in priority order)
1. **By epic** — if most stories have an `epic_id`, group by epic
2. **By label** — if stories have consistent labels (e.g. "API", "Dashboard", "Auth")
3. **By story type** — feature / bug / chore
4. **Flat** — if stories are too varied, just order by impact

### For each group, determine:
- A short **theme title** (e.g. "API Improvements", "User Onboarding")
- A suggested **demo order** (highest user-facing impact first)
- 2–3 **talking points** per story based on the name and description
- Any **stories to skip** in the demo (chores, minor fixes, internal-only work) — flag these and ask the user to confirm

### Present the plan in chat like:
```
## Demo Plan

### 1. Theme: API Improvements
- #123 — New rate limiting endpoint
  → Show the new /rate-limit endpoint, highlight the 429 response
- #145 — Improved error messages
  → Compare old vs new error format live

### 2. Theme: Dashboard
- #156 — New usage chart
  → Walk through the chart filters

---
Skipping (suggest omitting from demo):
- #134 — Dependency upgrade (chore, no user-visible change)
```

Ask the user: "Does this order look right? Anything to add, remove, or reorder?"

---

## Step 3: Generate the Presentation

Once the user confirms (or after making adjustments), follow the
**revealjs-presentation** skill to generate the slide deck.

### Slide structure for a demo deck:

1. **Title slide** — "Sprint Demo — [date range]", presenter name
2. **Agenda slide** — list of themes/sections
3. For each theme: **section divider slide** + one slide per story
4. **What's next** slide — optional, ask user if they want this
5. **Q&A / Thanks** closing slide

### Story slide content:
- Title = story name
- Body = 2–3 bullet talking points (from Step 2)
- Speaker notes = detailed demo script: what to click, what to show, what to say
- Labels shown as `.tag` elements in the corner

### Tone:
- This is an internal team demo — keep it clear and direct, not salesy
- Speaker notes should be practical ("navigate to X, click Y, show Z")

---

## Step 4: Deliver

Follow revealjs-presentation delivery steps:
- Save to `/mnt/user-data/outputs/demo-presentation.html`
- Share via `present_files`
- Remind user: arrow keys to navigate, `S` to open speaker notes view
