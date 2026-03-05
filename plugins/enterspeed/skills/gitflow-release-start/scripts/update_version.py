#!/usr/bin/env python3
"""Update majorVersion, minorVersion, patchVersion in an Azure Pipeline YAML file."""
import re
import os
import sys

major = os.environ["MAJOR"]
minor = os.environ["MINOR"]
patch = os.environ["PATCH"]
pipeline_file = os.environ["PIPELINE_FILE"]

content = open(pipeline_file).read()

updated = content
updated = re.sub(r'^(\s*majorVersion:\s*)\d+', r'\g<1>' + major, updated, flags=re.MULTILINE)
updated = re.sub(r'^(\s*minorVersion:\s*)\d+', r'\g<1>' + minor, updated, flags=re.MULTILINE)
updated = re.sub(r'^(\s*patchVersion:\s*)\d+', r'\g<1>' + patch, updated, flags=re.MULTILINE)

if updated == content:
    print(f"ERROR: No version keys were updated in {pipeline_file}. Check that majorVersion, minorVersion, and patchVersion exist.", file=sys.stderr)
    sys.exit(1)

open(pipeline_file, "w").write(updated)
print(f"Updated {pipeline_file} to {major}.{minor}.{patch}")
