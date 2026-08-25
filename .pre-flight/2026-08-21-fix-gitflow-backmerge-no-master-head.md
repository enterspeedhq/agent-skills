# fix/gitflow-backmerge-no-master-head — 2026-08-21

## Changed files

.claude-plugin/marketplace.json
plugins/enterspeed/skills/gitflow-release-finish/SKILL.md
plugins/enterspeed/skills/gitflow-release-publish/SKILL.md

## Observations

Step 3 was carrying a four-branch merge decision tree inside a step whose title is about opening a PR, against CONTRIBUTING's one-thing-per-step. Split into Step 3 (open the PR) and Step 4 (get it merged), with Step 5 doing verification and cleanup.

The Done summary asserted `develop: back-merged` and `release branch: deleted` unconditionally, which the `--auto` path can leave untrue when the session ends with the PR still queued. It now reports what actually happened and says plainly that a queued merge means the release isn't finished.

`backmerge/` is new branch vocabulary next to git flow's own `release/`. Kept deliberately — `git flow`'s namespaces are set in `git flow config` and `support/` already means something else — but worth a second opinion if the flow should stay inside git flow's naming.

Version goes to 1.18.0. #21 took 1.16.0 and #20 took 1.17.0, and on rebase git auto-resolved the identical 1.17.0 on both sides — which silently dropped the bump out of the diff altogether. Worth knowing that a version collision does not always show up as a conflict.
