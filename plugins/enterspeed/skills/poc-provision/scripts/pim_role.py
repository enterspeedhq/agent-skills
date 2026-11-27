#!/usr/bin/env python3
"""Create or remove an Azure role assignment through the PIM schedule APIs.

Builds the request body in Python so an ABAC condition never has to be
escaped in a shell, then calls the API via `az rest`.

Usage:
  python3 pim_role.py active   <scope> <principal-id> <role-guid> <end-date YYYY-MM-DD> <justification> [condition]
  python3 pim_role.py eligible <scope> <principal-id> <role-guid> <end-date YYYY-MM-DD> <justification> [condition]
  python3 pim_role.py remove-eligible <scope> <principal-id> <role-guid> <justification>

  active          time-bound active assignment (roleAssignmentScheduleRequests, AdminAssign)
  eligible        time-bound eligible assignment (roleEligibilityScheduleRequests, AdminAssign)
  remove-eligible removes an eligible assignment (roleEligibilityScheduleRequests, AdminRemove)

Exit code is az's exit code; az's output is printed as-is.
Requires Python 3.8+ and an authenticated Azure CLI.
"""
import datetime
import json
import shutil
import subprocess
import sys
import uuid

ENDPOINTS = {
    "active": ("roleAssignmentScheduleRequests", "AdminAssign"),
    "eligible": ("roleEligibilityScheduleRequests", "AdminAssign"),
    "remove-eligible": ("roleEligibilityScheduleRequests", "AdminRemove"),
}


def usage() -> int:
    print(__doc__, file=sys.stderr)
    return 2


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ENDPOINTS:
        return usage()
    mode, args = sys.argv[1], sys.argv[2:]
    removing = mode == "remove-eligible"
    if (removing and len(args) != 4) or (not removing and len(args) not in (5, 6)):
        return usage()

    if removing:
        scope, principal, role, justification = args
        end = condition = None
    else:
        scope, principal, role, end, justification = args[:5]
        condition = args[5] if len(args) == 6 else None
        try:
            datetime.date.fromisoformat(end)
        except ValueError:
            print(f"End date must be YYYY-MM-DD, got: {end}", file=sys.stderr)
            return 2

    az = shutil.which("az")  # resolves az.cmd on Windows
    if not az:
        print("Azure CLI (az) not found on PATH.", file=sys.stderr)
        return 2

    endpoint, request_type = ENDPOINTS[mode]
    props = {
        "principalId": principal,
        "roleDefinitionId": f"{scope}/providers/Microsoft.Authorization/roleDefinitions/{role}",
        "requestType": request_type,
        "justification": justification,
    }
    if not removing:
        props["scheduleInfo"] = {
            "startDateTime": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "expiration": {"type": "AfterDateTime", "endDateTime": f"{end}T23:59:59Z"},
        }
    if condition:
        props["condition"] = condition
        props["conditionVersion"] = "2.0"

    url = (
        f"https://management.azure.com{scope}/providers/Microsoft.Authorization/"
        f"{endpoint}/{uuid.uuid4()}?api-version=2020-10-01"
    )
    result = subprocess.run(
        [
            az, "rest", "--method", "put", "--url", url,
            "--body", json.dumps({"properties": props}),
            "--query", "{status:properties.status, type:properties.requestType, role:properties.roleDefinitionId, end:properties.scheduleInfo.expiration.endDateTime}",
            "-o", "json",
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout or result.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
