---
name: shortcut-publisher
description: Publish a user story to Shortcut for the Enterspeed Engineering team. Use when the user says "save to Shortcut", "create this in Shortcut", "add to Shortcut", "post to Shortcut", or "publish this story". Works on its own with a raw description, or after the enterspeed-user-stories skill has generated a formatted story.
---

# Shortcut Publisher

Posts a user story to the Enterspeed Engineering team's current iteration in Shortcut using the Shortcut MCP tools.

## How it works

1. If a formatted user story is already present in the conversation (from the `enterspeed-user-stories` skill or typed by the user), use it directly.
2. If only a raw feature description is given, ask the user: "Would you like me to generate a formatted user story first using the Enterspeed template, or publish with this raw description?" Generate if they agree; otherwise use the raw description as the story body.
3. Extract the title — the `**Title:**` line, without the `**Title:**` prefix. Leave that line out of the story body. If there is no title line, use the **"As a [role], I want [capability]"** line instead; if that is missing or malformed, reformat it before proceeding.
4. Extract the dependencies — the `**Blocked by** … · **Blocks** …` line, if present. Leave that line out of the story body too; *Resolve the dependencies* and *Create the story* below turn it into real Shortcut links.

## Prerequisites

If the Shortcut MCP tools are not available, guide the user to run the **shortcut-setup** skill first.

## Publishing via MCP

### 1. Get the workflow state ID

Call `list_workflows` and find the `Product Development` workflow. Locate the `Draft` state ID within it.

### 2. Get the current iteration ID

Call `get_current_iterations` and pick the most recently started iteration.

### 3. Get the Engineering team ID

Call `list_teams` and find the team named `Engineering`.

### 4. Resolve the dependencies

Resolve each story named in the dependency line to its ID with `get_story` (by ID) or `search_stories` (by name). If a named story can't be resolved, ask the user before creating anything rather than dropping it.

### 5. Create the story

Call `create_story` with:

```json
{
  "name": "<title from step 3 of How it works>",
  "description": "<full markdown story content, without the title and dependency lines>",
  "story_type": "feature",
  "workflow_state_id": <state_id>,
  "iteration_id": <iteration_id>,
  "team_id": <team_id>,
  "story_links": [
    { "verb": "blocks", "object_story_id": <id of a story this one Blocks> },
    { "verb": "blocks", "subject_story_id": <id of a story this one is Blocked by> }
  ]
}
```

The new story fills the side of each link that is left out. Omit `story_links` when there is no dependency line.

## After publishing

Show the user the story ID and URL as a clickable link. Confirm which iteration and team the story was added to (or note if these were not found).
