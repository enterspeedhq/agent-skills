---
name: shortcut-setup
version: 1.0.0
description: Set up the Shortcut API token securely using 1Password for the Enterspeed org. Use this skill whenever the user needs to configure their Shortcut API token, gets a SHORTCUT_API_TOKEN error, asks "how do I set up Shortcut", or is running a Shortcut skill for the first time. Referenced by shortcut-publisher, shortcut-summarizer, and shortcut-demo-planner.
---

# Shortcut Setup

One-time setup to securely store and auto-load the Shortcut API token using
1Password. Once done, all Shortcut skills will work without any further
configuration.

---

## When to use this skill

Guide the user through this setup if:
- Any Shortcut script prints `Error: SHORTCUT_API_TOKEN is not set`
- The user asks how to connect to Shortcut
- This is their first time using a Shortcut skill

Do **not** ask the user to paste or export the token as plain text.

---

## Setup steps

### 0. Install the 1Password CLI and enable desktop app integration

```bash
brew install 1password-cli
```

Then in the **1Password desktop app** → Settings → Developer → enable
**"Integrate with 1Password CLI"**. This allows the CLI to authenticate
silently through your existing desktop app session — no separate login needed.

---

### 1. Get your Shortcut API token

Go to: https://app.shortcut.com/enterspeed/settings/account/api-tokens

Generate a new token and copy it.

---

### 2. Store it in 1Password

```bash
op item create \
  --account enterspeed.1password.com \
  --category="API Credential" \
  --title="Shortcut API Token" \
  --vault="Private" \
  credential="your-token-here"
```

---

### 3. Add to `~/.zshrc`

```bash
export SHORTCUT_API_TOKEN=$(op item get "Shortcut API Token" --account enterspeed.1password.com --fields credential 2>/dev/null)
```

---

### 4. Reload your shell

```bash
source ~/.zshrc
```

---

## How it works after setup

The token is retrieved automatically each time a new shell session starts,
using your existing 1Password desktop app session. No extra biometric prompt
is needed. If 1Password is locked when the shell starts, the variable will be
empty and the Shortcut script will fail with a clear error — just unlock
1Password and open a new terminal.
