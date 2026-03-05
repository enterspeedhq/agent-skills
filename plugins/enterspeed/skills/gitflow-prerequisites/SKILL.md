---
name: gitflow-prerequisites
version: 1.1.0
description: Always invoke before gitflow-release-* or gitflow-hotfix-* skills. Verifies git flow installation, initialisation, git user identity, clean working directory, and branch state.
---

# Git Flow — Prerequisites

Verifies all common prerequisites for git flow skills. **Always run this first** before any `gitflow-release-*` or `gitflow-hotfix-*` skill.

> **Stop on any error** — if any check fails, report the issue to the user and do not proceed.

---

## Check 1 — git flow installed

```bash
git flow version
```

If this fails, stop and tell the user:

> "git flow is not installed. Install it with `brew install git-flow-avh` and run `git flow init` in your project first."

---

## Check 2 — git flow initialised

```bash
git flow config
```

If this fails, stop and tell the user:

> "git flow has not been initialised in this repository. Run `git flow init` first."

---

## Check 3 — git user identity configured

```bash
git config user.name
```

If this fails, stop and tell the user:

> "Git user.name is not configured. Set it with `git config user.name 'Your Name'`."

```bash
git config user.email
```

If this fails, stop and tell the user:

> "Git user.email is not configured. Set it with `git config user.email 'you@enterspeed.com'`."

---

## Check 4 — clean working directory

```bash
git status --porcelain
```

If there is any output, stop and tell the user:

> "There are uncommitted changes in your working directory. Please commit or stash them before continuing."

---

## Check 5 — verify you are on a branch (not detached HEAD)

```bash
git symbolic-ref -q HEAD
```

If this fails, stop and tell the user:

> "You are in detached HEAD state. Check out a branch (e.g. `git checkout develop`) before continuing."

---

## Done

All prerequisites passed successfully. Report success to the user and control returns to the calling skill. This skill does not return any value — it simply stops on any failure. If you reach this point, all checks have passed and the calling skill should continue with its next step.
