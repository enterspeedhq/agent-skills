---
name: merge-without-review
description: For engineers merging their own open pull request without an approving review (admin bypass) in a repo that requires review. Writes down why, so the reason lands in the merge commit. Use this skill whenever the user says "merge without review", "bypass review", "admin merge", "merge with bypass", "no reviewer available", "I need to merge this now", "merge without waiting for requirements", "skip the review on this PR", or asks how to document a bypass before merging. Not for writing justifications for PRs that are already merged. Requires the GitHub CLI (gh).
---

# Merge Without Review

Gets an engineer's own PR merged past the approval requirement with the reason written into the merge commit, in as few round trips as possible. A routine bypass is **one confirmation**. The only extra stop is a planned, non-urgent, high-risk change, where the skill asks once whether a review is worth it.

The engineer wants to get on with their work. Don't explain the policy, don't ask for anything you can read or infer, and don't confirm the same decision twice.

The policy lives in the **Development Process** doc in Shortcut, section "Branch protection and bypass":
https://app.shortcut.com/enterspeed/write/IkRvYyI6I3V1aWQgIjY1YWU2MTg3LTliYzgtNGExYS05NzY5LTA1MDAyNDNiMzQ0NyI=
If this skill ever disagrees with that doc, the doc wins.

---

## The policy (for you to reason with, not to recite)

| Case | What happens |
|---|---|
| **Low or medium risk:** release and back-merge PRs, docs, CI config, small contained fixes | Bypass. The reason explains the risk and how it was verified. |
| **Urgent fix:** production incident, customer blocked, a deadline that can't move | Bypass, then a **retrospective review** from a coworker. |
| **Planned, non-urgent and high risk:** deletes data, changes auth or permissions, affects all tenants, infrastructure | A review from the most relevant coworker is expected. The engineer can still bypass, but the reason must say why no review was possible. |

Being the only one who knows a repo is a valid reason there's no reviewer; the case still decides what else happens.

Template for the merge commit body:

```
Admin bypass, no review: <why it couldn't wait, or why review adds nothing>.
Risk is <low/medium/high>: <what the change touches and what it doesn't>.
Verified by: <tests, builds or manual runs that passed>.
```

---

## Step 1: Gather everything, silently

Fetch the PR the user named (number or URL), otherwise the current branch's:

```bash
gh pr view [<pr>] --json number,title,body,state,headRefOid,files,additions,deletions,reviewDecision,url
```

- No PR found: ask which one. This is the only question allowed in this step.
- Merged or closed: say the skill is for open PRs and stop.
- `reviewDecision` is `APPROVED`: nothing to bypass. Say so and stop.
- `reviewDecision` is empty: the repo doesn't require a review (a `baseline` repo), so there's nothing to bypass and no reason to record. Tell them to merge normally and stop.
- Continue only when `reviewDecision` is `REVIEW_REQUIRED` or `CHANGES_REQUESTED`.

Take `<owner/repo>` from the PR URL. Check what ran on the head commit:

```bash
gh api repos/<owner/repo>/commits/<headRefOid>/check-runs -q '.check_runs[] | .name + " | " + (.conclusion // .status)'
```

Then work out, without asking:

- **Case:** from the files, the PR title and body, and the user's own message. Urgency comes from words like hotfix, incident, prod, customer down or blocked, or a deadline. High risk comes from data deletion or migrations, auth, permissions or secrets, changes for every tenant, or infrastructure (Terraform, Bicep, networking, DNS, access policies).
- **Verification:** from the user's message ("tests pass locally"), the PR body (test counts, builds, environments) and the check-runs.
- **Retrospective reviewer** (urgent only): if the user named someone, use them.

If a `gh` call fails, carry on with what you have; gaps become placeholders in step 2.

---

## Step 2: One summary, one confirmation

Show a single message in this shape and nothing else:

```
PR #<n>: <title>
Case: <case>, <one short reason>
Checks: <"none ran" | "all passed" | "2 failing: build, lint">

Merge commit body:
  Admin bypass, no review: ...
  Risk is ...: ...
  Verified by: ...

Retrospective review: @<login>   (urgent only; or "@? — or skip, I'll ask in Slack")

Merge? (yes / edit the text / change the case)
```

Rules for the text:

- **Placeholders, not questions.** If something is missing, write it as `<tests run locally?>` or `<why it couldn't wait?>` in the draft. The engineer fills it in when they reply.
- **Be specific:** build or run numbers, test counts, which environment was checked.
- **No customer names** or identifiers (product numbers, tenant IDs). Write "one customer". This text is used as audit evidence.
- **Urgent fix:** end the first line with "Retrospective review will be requested from <name>." (or "from a coworker").
- **Failing checks:** if any check failed, the reason must say why merging anyway is safe. Make it a placeholder if you don't know.
- Three lines. A fourth only for something an auditor would ask about.

**High-risk, planned, non-urgent changes only:** replace the last line with:

```
This is the kind of change we usually get a second pair of eyes on.
Request a review from someone instead? (name them / no, merge anyway)
```

If they name someone, run `gh pr edit <pr> --repo <owner/repo> --add-reviewer <login>`, say it's done and stop. If they say merge anyway, make sure "Admin bypass, no review" says why no review was possible (a placeholder if they didn't say), show the updated body and ask "Merge?". This is the one case with a second confirmation.

If they edit the text or change the case, apply it and show only the changed part with "Merge?". Don't show the whole summary again.

---

## Step 3: Merge and finish

On "yes":

```bash
gh pr merge <pr> --repo <owner/repo> --admin --merge --body "$(cat <<'EOF'
Admin bypass, no review: ...
Risk is ...: ...
Verified by: ...
EOF
)"
```

Leave `--subject` out so GitHub keeps its default subject. If GitHub says merge commits aren't allowed on the repo, retry once with `--squash` (it keeps the body). If the merge fails:

- **Permission error:** they don't have Maintain or Admin on this repo, so they can't bypass. Say so in one line, suggest asking a coworker to review, and stop.
- **Anything else** (conflicts, branch out of date): show the error and stop.

For urgent fixes with a named reviewer, post the retrospective review request straight away. It was already confirmed in step 2:

```bash
gh pr comment <pr> --repo <owner/repo> --body "@<login> could you do a retrospective review of this? It was merged without review as an urgent fix; the reason is in the merge commit."
```

If they chose to ask in Slack, don't post.

Finish with one line:

```
Merged: <url> (<short sha>)
```

For urgent fixes, add "Retrospective review requested from @<login>", or "Remember to ask for the retrospective review" if they chose Slack. Nothing else.
