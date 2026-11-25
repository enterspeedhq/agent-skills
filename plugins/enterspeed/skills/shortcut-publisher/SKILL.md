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
5. Strip the assumptions — remove everything from the `### 💭 Assumptions Made` heading onwards, including the `---` rule just above it. It is a note to the person reviewing the draft, not part of the story.

## Prerequisites

If the Shortcut MCP tools are not available, guide the user to run the **shortcut-setup** skill first.

## Publishing via MCP

### 1. Get the workflow state ID

Call `list_workflows` and find the `Product Development` workflow. Locate the `Draft` state ID within it. Use this workflow for every team in step 3, including `Customer Success`: that team also has its own `Customer Success` workflow, which is for the customer success team's non-engineering tasks, not for engineering stories.

### 2. Get the current iteration ID

Call `get_current_iterations` and pick the most recently started iteration.

### 3. Pick the team

Each product has its own team, and the story goes on the board of the product it changes. The repo the story changes decides the team:

| Team | Repos |
|---|---|
| `Graph` | `semantic-graph`, `semantic-graph-sdk`, `graph-contracts`, `merchant-feeds`, `gmc-feed-builder`, `enterspeed-feed-builder`, `enterspeed-context-graph-customer-demo-frontend`; `n8n-nodes-enterspeed` when the node works with the graph |
| `Platform` | `platform`, `infrastructure`, `enterspeed-js-mapping-api`, `enterspeed-js-schema-types`, `enterspeed-management-app`, `enterspeed-management-frontend`, `enterspeed-mcp`, `enterspeed-sdk-*`, `enterspeed-cli`, `enterspeed-smoke-tests`, `enterspeed-elastic-heartbeat`, `enterspeed-b2c-userflow`, `enterspeed-scheduled-*`, `enterspeed-customer-demo-frontend`, `load-tests`, `ingest-helper`, `enterspeed-migrator`, `enterspeed-schema-specs`, `enterspeed-view-data-extensions`, `query-mcp-agent`, `enterspeed-query-mcp-demo`; **every destination** (`enterspeed-destination-*`, `bestseller-enterspeed-destination-syndigo`) and **every ingester** (`*-ingester`, e.g. `alfa-laval-enterspeed-ingester`, `bestseller-syndigo-ingester`) |
| `Speedtrain` | `speedtrain`, `speedtrain-*` (app, mcp, infrastructure, smoke-tests and the rest), `spt-tenant-producer-poc`, `enterspeed-speedtrain-demo-site` |
| `Customer Success` | customer repos: `alfa-laval-anonymiser`, `bestseller-*` feeds, `bolia-*`, `palsgaard-questionaires`, `mypalsgaard-blob-enterspeed`, `supplier-portal`, `supplier-portal-app`, `gs1`, `stark-matching-learnings`, `ee-contract-uploader`, `salling-group-migration`, `enterspeed-salling-product-cloud`, `bygningsreglementet-migrering`; connectors: `enterspeed-source-*`, `enterspeed-plugins-umbraco-cms`, `enterspeed-umbraco-query-picker`, `enterspeed-shopify`, `enterspeed-connector-template` |
| `Engineering` | `agent-skills`, `enterspeed-skills`, `enterspeed-docs`, `scripts`, `sbom`, `azure-cost-alerts`, `es-history`, `pipelines-poc`, `hamsterbox-runner`, `enterspeed.com`, `drop`, `fetch`, `ai-readiness-*`, `V2X-*`, `poc-*`, `enterspeed-perfection-poc`; `n8n-nodes-enterspeed` when the node does not touch the graph |

A destination or ingester goes on `Platform` even when it is built for one customer. Both `Graph` and `Platform` have services called ingest, processing, delivery, management and MCP, so a service name never decides between them; the repo does.

If the story names no repo, use its epic's team. If the story names both a repo and an epic, and the epic's team differs from the repo's team, ask the user which of the two teams before creating the story, suggesting the repo's team. If the repo isn't in the table, the story names neither a repo nor an epic, or it changes repos on two boards, ask the user which team, and offer `Engineering` as the suggested answer, the catch-all board. Don't put the story on `Engineering` until the user has answered.

`list_teams` also returns teams that are not product boards. `Agentic Product Cloud` comes in only through an epic's team or when the user names it, and a mismatch with the repo's team is asked about as above. Never pick the `Hamster` team (a workflow experiment) unless the user asks for it.

Call `list_teams` and take the ID of the chosen team. If no team with that name exists, stop and tell the user rather than picking another.

### 4. Resolve the dependencies

Resolve each story named in the dependency line to its ID with `get_story` (by ID) or `search_stories` (by name). If a named story can't be resolved, ask the user before creating anything rather than dropping it.

### 5. Create the story

Call `create_story` with:

```json
{
  "name": "<title from step 3 of How it works>",
  "description": "<full markdown story content, without the title, dependency line and assumptions block>",
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
