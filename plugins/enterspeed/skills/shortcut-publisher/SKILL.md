---
name: shortcut-publisher
version: 1.0.0
description: Publish a user story to Shortcut for the Enterspeed Engineering team. Use when the user says "save to Shortcut", "create this in Shortcut", "add to Shortcut", "post to Shortcut", or "publish this story". Works on its own with a raw description, or after the enterspeed-user-stories skill has generated a formatted story.
---

# Shortcut Publisher

Posts a user story to the Enterspeed Engineering team's current iteration in Shortcut, using the Product Development workflow.

## How it works

1. If a formatted user story is already present in the conversation (from the `enterspeed-user-stories` skill or typed by the user), use it directly.
2. If only a raw feature description is given, ask the user: "Would you like me to generate a formatted user story first using the Enterspeed template, or publish with this raw description?" Generate if they agree; otherwise use the raw description as the story body.
3. Validate the story has an **"As a [role], I want [capability]"** line to use as the title. If it's missing or malformed, reformat it before proceeding.
4. Extract the title — the **"As a [role], I want [capability]"** line.
5. Use the script below to post the story to Shortcut.

## Running the script

Write the following script to `/tmp/create_story.py`, then execute it:

```python
#!/usr/bin/env python3
import argparse, json, os, sys, urllib.request, urllib.error

BASE_URL = "https://api.app.shortcut.com/api/v3"
WORKFLOW_NAME = "Product Development"
TEAM_NAME = "Engineering"
DEFAULT_STATE = "Draft"

def api(method, path, data=None):
    token = os.environ.get("SHORTCUT_API_TOKEN")
    if not token:
        print("Error: SHORTCUT_API_TOKEN not set.")
        print("Get your token at: https://app.shortcut.com/enterspeed/settings/account/api-tokens")
        sys.exit(1)
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json", "Shortcut-Token": token}
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"HTTP error {e.code}: {e.read().decode()}")
        sys.exit(1)

def get_workflow_state_id():
    for wf in api("GET", "/workflows"):
        if wf["name"] == WORKFLOW_NAME:
            for state in wf["states"]:
                if state["name"] == DEFAULT_STATE:
                    return wf["id"], state["id"]
    print(f"Could not find workflow '{WORKFLOW_NAME}' or state '{DEFAULT_STATE}'.")
    sys.exit(1)

def get_current_iteration_id():
    active = [i for i in api("GET", "/iterations") if i.get("status") == "started"]
    if not active:
        return None
    active.sort(key=lambda i: i.get("start_date", ""), reverse=True)
    return active[0]["id"]

def get_team_id():
    for g in api("GET", "/groups"):
        if g["name"] == TEAM_NAME:
            return g["id"]
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    args = parser.parse_args()

    _, state_id = get_workflow_state_id()
    iteration_id = get_current_iteration_id()
    team_id = get_team_id()

    payload = {
        "name": args.title,
        "description": args.description,
        "story_type": "feature",
        "workflow_state_id": state_id,
    }
    if iteration_id:
        payload["iteration_id"] = iteration_id
    if team_id:
        payload["group_id"] = team_id

    story = api("POST", "/stories", payload)
    print(f"\n✅ Story created!")
    print(f"   ID:  #{story.get('id', '')}")
    print(f"   URL: {story.get('app_url', '')}")

if __name__ == "__main__":
    main()
```

Run it with:

```bash
python3 /tmp/create_story.py \
  --title "<As a [role], I want [capability]>" \
  --description "<full markdown story content>"
```

## Required environment variable

The script reads `SHORTCUT_API_TOKEN` from the environment. If it is not set,
the script will print an error and exit. In that case, proactively guide the
user to run the **shortcut-setup** skill first. Do not ask the user to export
the token as plain text.

## After publishing

Read the script output and present the result to the user in a friendly way:
- Show the story ID and the Shortcut URL as a clickable link
- Confirm which iteration and team the story was added to (or note if these were not found)
