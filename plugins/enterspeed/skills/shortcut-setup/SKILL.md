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

**macOS (requires Homebrew):**
```bash
brew install 1password-cli
```

**Linux / Windows:** See [1Password CLI installation docs](https://developer.1password.com/docs/cli/get-started/) for platform-specific instructions.

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

### 3. Add to your shell profile

Add the following to your shell's startup file (`~/.zshrc` for Zsh, `~/.bashrc` or `~/.bash_profile` for Bash, or `~/.config/fish/config.fish` for Fish):

```bash
export SHORTCUT_API_TOKEN=$(op item get "Shortcut API Token" --account enterspeed.1password.com --fields credential)
```

To verify it works after reloading:
```bash
echo $SHORTCUT_API_TOKEN
```
You should see your token. If the output is empty, see the troubleshooting section below.

---

### 4. Reload your shell

```bash
source ~/.zshrc
```

---

## How it works after setup

The token is retrieved automatically each time a new shell session starts,
using your existing 1Password desktop app session. No extra biometric prompt
is needed.

---

## Troubleshooting

**Token is empty after setup:**
1Password was likely locked when the shell started. Unlock 1Password and open a new terminal — the token will be retrieved on the next shell launch.

**`op` command not found:**
The 1Password CLI is not installed or not on your PATH. Re-run Step 0.

**`op item get` returns an error:**
Run the command manually without output redirection to see the full error:
```bash
op item get "Shortcut API Token" --account enterspeed.1password.com --fields credential
```
Common causes: wrong item name, wrong vault, or desktop app integration not enabled.
