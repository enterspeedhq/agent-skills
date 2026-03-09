---
name: pre-flight
description: Run a self-check on your current changes before raising a PR. Use when the user says "pre-flight", "run pre-flight", "check my changes", "sanity check", "self-review", "am I ready to raise a PR", or "check my branch".
---

# Pre-flight

A quick look at your current changes before you put them in front of others. Surfaces things worth considering — not a verdict, not a gate.

---

## Step 1: Get the diff

Identify the base branch:

```bash
git rev-parse --abbrev-ref HEAD
git remote show origin | grep 'HEAD branch'
```

Then diff against it:

```bash
git diff origin/<base-branch>...HEAD
git diff origin/<base-branch>...HEAD --name-only --diff-filter=ACMRT
```

Also check for unstaged changes:

```bash
git status --short
```

If the branch is clean and nothing is ahead of base, tell the user:

> "Nothing to check — no changes ahead of `<base-branch>`."

---

## Step 2: Gauge the size

Count changed files (excluding lock files and generated files):

- **Focused (< 15 files):** Read all changes in full
- **Medium (15–50 files):** Read new files fully, sample the most-changed existing files, skip lock files, generated code, and formatting-only changes
- **Large (50+ files):** Focus on new files and the heaviest changes; note if the PR appears to mix unrelated concerns

State which mode briefly and move on: *"12 files — reading everything."*

---

## Step 3: Find team patterns

Look for any of these. Read what exists:

- `CONTRIBUTING.md`
- `DEVELOPMENT.md`
- `CODE_STYLE.md`
- `CODING_STANDARDS.md`
- `docs/architecture.md`
- `docs/architecture/` (any `.md` files within)
- `docs/*-guidelines.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `CLAUDE.md` (team AI conventions)

Note which sections are relevant to what changed. If nothing exists, proceed — general good practices still apply.

---

## Step 4: Read the changes

Read the changed files with enough surrounding context to understand intent, not just the diff lines in isolation.

Skip: lock files, generated files, build output, pure formatting changes.

---

## Step 5: Surface observations

For each thing worth noting, write a short observation. Each observation must:

- Describe what you noticed, concretely — file name and line range where useful
- Ask a question that invites the developer to consider whether it's intentional
- Never tell them what to do

**Format:** Two sentences maximum per observation. First sentence: what you saw. Second sentence: the question.

**Things worth noticing** — only raise these when they genuinely stand out, not as a checklist:

- Something differs from a documented team pattern: *"X uses Y — the team has landed on Z for this. Different approach intentional, or worth aligning?"*
- Logic that's harder to follow than it needs to be: *"This function has four exit points. Anything driving that shape?"*
- A logic path with no test coverage: *"This error case isn't covered. Happy to leave it, or worth a test?"*
- Names that don't communicate what they hold or do: *"What does `data` contain at this point?"*
- A change that touches more than its stated scope: *"This modifies the base class — anything else relies on this behavior?"*
- Loose ends that may be unintentional: *"TODO on line 42 — for this PR or a follow-up?"*

Do not manufacture observations. If nothing stands out, that's a valid result.

---

## Step 6: Close

If observations exist, lead with a brief count:

> "Three things worth a look."

Then list them.

If nothing stood out:

> "Nothing jumped out. Looks clean."

No verdict. No score. No "you're good to go" or "this needs work."

---

## Step 7: Write the log

Write a record to `.pre-flight/<YYYY-MM-DD>-<branch-name>.md`, creating the `.pre-flight/` directory if it doesn't exist.

```bash
mkdir -p .pre-flight
```

The file format:

```markdown
# <branch-name> — <YYYY-MM-DD HH:MM>

## Changed files
<list of changed files, one per line>

## Observations
<each observation exactly as shown to the developer, or "None." if nothing stood out>
```

Write only what was surfaced to the developer — no internal notes, no categories, no extra metadata.

Tell the user the file was written and where:

> "Log written to `.pre-flight/<filename>`. Review it before committing — edit out anything you don't want to share."
