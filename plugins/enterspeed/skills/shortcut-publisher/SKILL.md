---
name: shortcut-publisher
description: Publish a user story to Shortcut on the right Enterspeed product team (Graph, Platform, Speedtrain, Customer Success, or Engineering). Use when the user says "save to Shortcut", "create this in Shortcut", "add to Shortcut", "post to Shortcut", or "publish this story". Works on its own with a raw description, or after the enterspeed-user-stories skill has generated a formatted story.
---

# Shortcut Publisher

Posts a user story to the current iteration in Shortcut, on the team for the product it belongs to, using the Shortcut MCP tools.

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

### 3. Pick the team

Each product has its own team, and the story goes on the board of the product it changes:

| Team | The story is about |
|---|---|
| `Graph` | semantic-graph, the graph SDK and dev server, the graph MCP, merchant feeds, n8n work for the graph, anything under a Context Graph epic or objective, and work where Speedtrain meets the graph (source-domain ingest, the factory as a registered consumer, writeback) |
| `Platform` | platform (ingest, processing, delivery), infrastructure, the JS mapping API, the management app, the Query and Management MCPs, the Core SDKs and CLI, production compliance work |
| `Speedtrain` | speedtrain, speedtrain-app, speedtrain-mcp, speedtrain infrastructure, the Session Manager |
| `Customer Success` | a customer integration project or connector (a named customer, Shopify, Umbraco, Sitecore) |
| `Engineering` | internal work: ISMS and Vanta, access reviews, onboarding, tooling, agent skills, process, PoCs |

Work it out from the repo, epic or product the story names. If the story has an epic, the epic's team usually decides it. If two teams fit, or none clearly does, ask the user which team before creating the story rather than defaulting to `Engineering`.

Call `list_teams` and take the ID of the chosen team. If no team with that name exists, stop and tell the user rather than picking another.

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

Show the user the story ID and URL as a clickable link. Confirm which iteration and team the story was added to, and why that team (or note if these were not found).
