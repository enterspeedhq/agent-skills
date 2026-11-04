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
4. Extract the dependencies — the `**Blocked by** … · **Blocks** …` line, if present. Leave that line out of the story body too; *Link the dependencies* below turns it into real Shortcut links.

## Prerequisites

If the Shortcut MCP tools are not available, guide the user to run the **shortcut-setup** skill first.

## Publishing via MCP

### 1. Get the workflow state ID

Call `workflows-list` and find the `Product Development` workflow. Locate the `Draft` state ID within it.

### 2. Get the current iteration ID

Call `iterations-get-active` and pick the most recently started iteration.

### 3. Get the Engineering team ID

Call `teams-list` and find the team named `Engineering`.

### 4. Create the story

Call `stories-create` with:

```json
{
  "name": "<title from step 3>",
  "description": "<full markdown story content, without the title and dependency lines>",
  "story_type": "feature",
  "workflow_state_id": <state_id>,
  "iteration_id": <iteration_id>,
  "group_id": <team_id>
}
```

### 5. Link the dependencies

For each story named in the dependency line, call the Shortcut MCP's story-link tool with the verb `blocks`: the new story as subject for **Blocks**, as object for **Blocked by**. If a named story can't be resolved to an ID, ask the user rather than dropping it.

## After publishing

Show the user the story ID and URL as a clickable link. Confirm which iteration and team the story was added to (or note if these were not found).
