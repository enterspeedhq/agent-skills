---
name: shortcut-publisher
version: 1.0.0
description: Publish a user story to Shortcut for the Enterspeed Engineering team. Use when the user says "save to Shortcut", "create this in Shortcut", "add to Shortcut", "post to Shortcut", or "publish this story". Works on its own with a raw description, or after the enterspeed-user-stories skill has generated a formatted story.
---

# Shortcut Publisher

Posts a user story to the Enterspeed Engineering team's current iteration in Shortcut, using the Product Development workflow.

## How it works

1. If a formatted user story is already present in the conversation (from the `enterspeed-user-stories` skill or typed by the user), use it directly.
2. If only a raw feature description is given, first generate the story using the Enterspeed user story format (see `enterspeed-user-stories` skill), then publish.
3. Extract the title — this is the **"As a [role], I want [capability]"** line from the story.
4. Use the script below to post the story to Shortcut.

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
follow the **shortcut-setup** skill for step-by-step instructions on securely
storing and auto-loading the token via 1Password. Do not ask the user to export
the token as plain text.

## After publishing

Show the user the Shortcut story URL returned by the script so they can navigate directly to the created story.
