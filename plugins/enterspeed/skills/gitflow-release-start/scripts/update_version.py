#!/usr/bin/env python3
"""Update majorVersion, minorVersion, patchVersion in an Azure Pipeline YAML file."""
import re
import os
import sys

try:
    major = os.environ["MAJOR"]
    minor = os.environ["MINOR"]
    patch = os.environ["PATCH"]
    pipeline_file = os.environ["PIPELINE_FILE"]
except KeyError as e:
    print(f"ERROR: Missing required environment variable: {e}", file=sys.stderr)
    sys.exit(1)

try:
    with open(pipeline_file, "r") as f:
        content = f.read()
except FileNotFoundError:
    print(f"ERROR: Pipeline file not found: {pipeline_file}", file=sys.stderr)
    sys.exit(1)
except PermissionError:
    print(f"ERROR: Permission denied reading file: {pipeline_file}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Failed to read {pipeline_file}: {e}", file=sys.stderr)
    sys.exit(1)

updated = content
updated = re.sub(r'^(\s*majorVersion:\s*)\d+', r'\g<1>' + major, updated, flags=re.MULTILINE)
updated = re.sub(r'^(\s*minorVersion:\s*)\d+', r'\g<1>' + minor, updated, flags=re.MULTILINE)
updated = re.sub(r'^(\s*patchVersion:\s*)\d+', r'\g<1>' + patch, updated, flags=re.MULTILINE)

if updated == content:
    print(f"ERROR: No version keys were updated in {pipeline_file}. Check that majorVersion, minorVersion, and patchVersion exist.", file=sys.stderr)
    sys.exit(1)

try:
    with open(pipeline_file, "w") as f:
        f.write(updated)
except PermissionError:
    print(f"ERROR: Permission denied writing to file: {pipeline_file}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Failed to write {pipeline_file}: {e}", file=sys.stderr)
    sys.exit(1)

print(f"Updated {pipeline_file} to {major}.{minor}.{patch}")
