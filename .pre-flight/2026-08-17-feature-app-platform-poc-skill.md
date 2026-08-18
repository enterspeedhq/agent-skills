# feature/app-platform-poc-skill — 2026-08-17

## Changed files

.claude-plugin/marketplace.json
plugins/enterspeed/skills/app-platform-poc/SKILL.md
plugins/enterspeed/skills/app-platform-poc/references/app-platform-blueprint.md
plugins/enterspeed/skills/app-platform-poc/references/appendix-a-auth.md
plugins/enterspeed/skills/app-platform-poc/references/appendix-b-database.md

## Observations

The blueprint was executed end to end twice before this log was written — once as a database-backed
tool, once adding auth to that same tool — so the embedded code builds, runs, migrates, authenticates
and passes its own tests. The observations below are the parts a local run can't reach.

`ci.yml` is the one generated artefact that can't be verified here — no GitHub in the loop. Its most likely failure mode (a hardcoded Node version) is gone now that CI reads `.nvmrc`. Ship it unverified, or dry-run it on a throwaway repo first?

The skill was exercised by following its files directly, not by invoking it as an installed plugin, so `<skill-path>` resolution and description-based triggering are still unproven. Worth installing the branch as a local marketplace to confirm, or acceptable to find out on first real use?

Six existing skills still carry a `version:` field in frontmatter, which `CLAUDE.md` now tells us not to add; this one omits it. Is the rule newer than those files, and are they worth a separate tidy-up PR?

Parts of the blueprint no test tool touched: file uploads and `apiPostForm`, snake_case serialisation for external contracts, golden-file tests, `WebApplicationFactory` integration tests, the preview/`dryRun` shape, applying the Terraform skeleton, mid-session token expiry, and the `Admin2` seeding slot. Fine as untested surface, or worth a second PoC shaped to hit the upload path?
