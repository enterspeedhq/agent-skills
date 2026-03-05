---
name: gitflow-prerequisites
version: 1.0.0
description: Verify that git flow prerequisites are met for an Enterspeed project. Checks git flow installation, initialisation, git user identity, clean working directory, and branch state. Run at the start of any gitflow-release-* or gitflow-hotfix-* skill before proceeding.
---

# Git Flow — Prerequisites

Verifies all common prerequisites for git flow skills. Run this before any `gitflow-release-*` or `gitflow-hotfix-*` skill.

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
git config user.name && git config user.email
```

If either fails, stop and tell the user:
> "Git user identity is not configured. Set it with `git config user.name 'Your Name'` and `git config user.email 'you@enterspeed.com'`."

---

## Check 4 — clean working directory

```bash
git status --porcelain
```

If there is any output, stop and tell the user:
> "There are uncommitted changes in your working directory. Please commit or stash them before continuing."

---

## Check 5 — not in detached HEAD state

```bash
git symbolic-ref -q HEAD
```

If this fails, stop and tell the user:
> "You are in detached HEAD state. Check out a branch (e.g. `git checkout develop`) before continuing."

---

## Done

All prerequisites passed. Return to the skill that triggered this check and continue with the next step.
