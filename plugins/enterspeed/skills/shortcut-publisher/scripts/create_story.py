#!/usr/bin/env python3
"""
Creates a user story in Shortcut for the Enterspeed Engineering team.
Targets the current iteration of the Product Development workflow.
Usage:
    python3 create_story.py --title "..." --description "..."
Environment:
    SHORTCUT_API_TOKEN  Your Shortcut API token
                        Get it at: https://app.shortcut.com/enterspeed/settings/account/api-tokens
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

BASE_URL = "https://api.app.shortcut.com/api/v3"
WORKFLOW_NAME = "Product Development"
TEAM_NAME = "Engineering"
DEFAULT_STATE = "Draft"


def api(method, path, data=None):
    token = os.environ.get("SHORTCUT_API_TOKEN")
    if not token:
        print("Error: SHORTCUT_API_TOKEN environment variable not set.")
        print("Get your token at: https://app.shortcut.com/enterspeed/settings/account/api-tokens")
        sys.exit(1)

    url = f"{BASE_URL}{path}"
    headers = {
        "Content-Type": "application/json",
        "Shortcut-Token": token,
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"HTTP error {e.code}: {e.read().decode()}")
        sys.exit(1)


def get_workflow_state_id():
    workflows = api("GET", "/workflows")
    for wf in workflows:
        if wf["name"] == WORKFLOW_NAME:
            for state in wf["states"]:
                if state["name"] == DEFAULT_STATE:
                    return wf["id"], state["id"]
    print(f"Could not find workflow '{WORKFLOW_NAME}' or state '{DEFAULT_STATE}'.")
    sys.exit(1)


def get_current_iteration_id():
    iterations = api("GET", "/iterations")
    active = [i for i in iterations if i.get("status") == "started"]
    if not active:
        print("No active iteration found. Story will be created without an iteration.")
        return None
    active.sort(key=lambda i: i.get("start_date", ""), reverse=True)
    return active[0]["id"]


def get_team_id():
    groups = api("GET", "/groups")
    for g in groups:
        if g["name"] == TEAM_NAME:
            return g["id"]
    print(f"Warning: Could not find team '{TEAM_NAME}'. Story will be created without a team.")
    return None


def create_story(title, description):
    workflow_id, state_id = get_workflow_state_id()
    iteration_id = get_current_iteration_id()
    team_id = get_team_id()

    payload = {
        "name": title,
        "description": description,
        "story_type": "feature",
        "workflow_state_id": state_id,
    }
    if iteration_id:
        payload["iteration_id"] = iteration_id
    if team_id:
        payload["group_id"] = team_id

    story = api("POST", "/stories", payload)
    return story


def main():
    parser = argparse.ArgumentParser(description="Create a Shortcut story for Enterspeed Engineering.")
    parser.add_argument("--title", required=True, help="Story title (e.g. 'As a developer, I want...')")
    parser.add_argument("--description", required=True, help="Full markdown story content")
    args = parser.parse_args()

    print(f"Creating story: {args.title}")
    story = create_story(args.title, args.description)
    url = story.get("app_url", "")
    sid = story.get("id", "")
    print(f"\n✅ Story created successfully!")
    print(f"   ID:  #{sid}")
    print(f"   URL: {url}")


if __name__ == "__main__":
    main()
