#!/usr/bin/env python3
"""
Fetch Shortcut stories by owner, time range, workflow state, group, and iteration.

Usage:
  python3 fetch_stories.py [--weeks N] [--state STATE] [--owner NAME|me|team]
                           [--group GROUP_NAME] [--iteration ITERATION_NAME]
                           [--with-details]

Output: JSON to stdout, save to /tmp/shortcut_stories.json for use by other skills.
"""
import argparse, json, os, sys, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

BASE_URL = "https://api.app.shortcut.com/api/v3"


def api(method, path, data=None):
    token = os.environ.get("SHORTCUT_API_TOKEN")
    if not token:
        print("Error: SHORTCUT_API_TOKEN is not set.")
        print("Follow the shortcut-setup skill to configure it securely via 1Password.")
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


def get_current_member():
    m = api("GET", "/member")
    # API v3 returns name at top level; fall back to profile.name for older responses
    member_name = m.get("name") or m.get("profile", {}).get("name", "Unknown")
    return m["id"], member_name


def get_member_by_name(name):
    members = api("GET", "/members")
    name_lower = name.lower()
    for m in members:
        member_name = m.get("name") or m.get("profile", {}).get("name", "")
        if name_lower in member_name.lower():
            return m["id"], member_name
    return None, None


def get_group_by_name(name):
    groups = api("GET", "/groups")
    name_lower = name.lower()
    for g in groups:
        if name_lower in g.get("name", "").lower():
            return g["id"], g["name"]
    return None, None


def get_iteration_by_name(name):
    iterations = api("GET", "/iterations")
    name_lower = name.lower()
    matches = [i for i in iterations if name_lower in i.get("name", "").lower()]
    if not matches:
        return None, None
    # Prefer started/in-progress, then most recent by start_date
    for status in ("started", "unstarted", "done"):
        for it in sorted(matches, key=lambda x: x.get("start_date", ""), reverse=True):
            if it.get("status") == status:
                return it["id"], it["name"]
    matches.sort(key=lambda x: x.get("start_date", ""), reverse=True)
    return matches[0]["id"], matches[0]["name"]


def get_matching_state_ids(state_type_hint):
    """
    state_type_hint: 'done', or a name fragment like 'in development', 'ready for review'.
    Returns list of (workflow_state_id, state_name) tuples.
    """
    matches = []
    for wf in api("GET", "/workflows"):
        for state in wf["states"]:
            if state_type_hint == "done":
                if state["type"] == "done":
                    matches.append((state["id"], state["name"]))
            else:
                if state_type_hint.lower() in state["name"].lower():
                    matches.append((state["id"], state["name"]))
    return matches


def main():
    parser = argparse.ArgumentParser(description="Fetch Shortcut stories.")
    parser.add_argument("--weeks", type=int, default=4, help="How many weeks back to look (default: 4)")
    parser.add_argument("--state", default="done", help="State type or name fragment: 'done', 'in development', 'ready for review', etc.")
    parser.add_argument("--owner", default="me", help="'me' (default), 'team', or a member name")
    parser.add_argument("--group", default=None, help="Filter by team/group name, e.g. 'Engineering'")
    parser.add_argument("--iteration", default=None, help="Filter by iteration name, e.g. 'Continues Kanban'")
    parser.add_argument("--with-details", action="store_true", help="Fetch full story details (description, PRs) via individual API calls")
    args = parser.parse_args()

    cutoff = datetime.now(timezone.utc) - timedelta(weeks=args.weeks)

    # Resolve owner
    if args.owner == "me":
        member_id, member_name = get_current_member()
        owner_label = member_name
    elif args.owner == "team":
        member_id = None
        owner_label = "the whole team"
    else:
        member_id, member_name = get_member_by_name(args.owner)
        if not member_id:
            print(f"Could not find member matching '{args.owner}'")
            sys.exit(1)
        owner_label = member_name

    # Resolve group
    group_id = None
    group_label = None
    if args.group:
        group_id, group_label = get_group_by_name(args.group)
        if not group_id:
            print(f"Could not find group matching '{args.group}'")
            sys.exit(1)

    # Resolve iteration
    iteration_id = None
    iteration_label = None
    if args.iteration:
        iteration_id, iteration_label = get_iteration_by_name(args.iteration)
        if not iteration_id:
            print(f"Could not find iteration matching '{args.iteration}'")
            sys.exit(1)

    # Resolve states
    state_matches = get_matching_state_ids(args.state)
    if not state_matches:
        print(f"No workflow states found matching '{args.state}'")
        sys.exit(1)
    state_ids = {sid for sid, _ in state_matches}
    state_label = ", ".join(sorted({sname for _, sname in state_matches}))

    # Build search payload
    search_payload = {"archived": False}
    if member_id:
        search_payload["owner_ids"] = [member_id]
    if group_id:
        search_payload["group_id"] = group_id
    if iteration_id:
        search_payload["iteration_id"] = iteration_id
    if args.state == "done":
        search_payload["workflow_state_types"] = ["done"]
    elif len(state_ids) == 1:
        # Pass the specific state ID when there's an unambiguous match
        search_payload["workflow_state_id"] = list(state_ids)[0]

    result = api("POST", "/stories/search", search_payload)
    stories = result if isinstance(result, list) else result.get("data", [])

    # Post-filter by state IDs (catches multi-state matches and any API drift)
    filtered = []
    for story in stories:
        if story.get("workflow_state_id") not in state_ids:
            continue
        ts = story.get("completed_at") or story.get("updated_at", "")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        if dt < cutoff:
            continue
        filtered.append({
            "id": story.get("id"),
            "name": story.get("name"),
            "description": (story.get("description") or "").strip(),
            "story_type": story.get("story_type", "feature"),
            "workflow_state_id": story.get("workflow_state_id"),
            "owner_ids": story.get("owner_ids", []),
            "completed_at": story.get("completed_at", ts),
            "updated_at": ts,
            "url": story.get("app_url", ""),
            "labels": [l["name"] for l in story.get("labels", [])],
            "epic_id": story.get("epic_id"),
            "group_id": story.get("group_id"),
            "iteration_id": story.get("iteration_id"),
        })

    # Optionally fetch individual story details (full description + PRs)
    # Only when --with-details is passed, as it makes one API call per story
    if args.with_details:
        for story in filtered:
            detail = api("GET", f"/stories/{story['id']}")
            story["description"] = (detail.get("description") or "").strip()
            story["pull_requests"] = [
                {
                    "url": pr["url"],
                    "number": pr["number"],
                    "title": pr["title"],
                    "merged": pr.get("merged", False),
                    "draft": pr.get("draft", False),
                    "review_status": pr.get("review_status"),
                    "build_status": pr.get("build_status"),
                }
                for pr in detail.get("pull_requests", [])
            ]

    # Resolve member names for owner display
    if any(s["owner_ids"] for s in filtered):
        all_members = api("GET", "/members")
        member_map = {m["id"]: (m.get("name") or m.get("profile", {}).get("name", "Unknown")) for m in all_members}
        for story in filtered:
            story["owners"] = [member_map.get(oid, oid) for oid in story["owner_ids"]]
    else:
        for story in filtered:
            story["owners"] = []

    output = {
        "owner": owner_label,
        "group": group_label,
        "iteration": iteration_label,
        "weeks": args.weeks,
        "state": state_label,
        "story_count": len(filtered),
        "stories": filtered,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
