# feature/app-platform-poc-environment — 2026-11-27

## Changed files

.claude-plugin/marketplace.json
plugins/enterspeed/skills/app-platform-poc/SKILL.md
plugins/enterspeed/skills/app-platform-poc/references/app-platform-blueprint.md
plugins/enterspeed/skills/app-platform-poc/references/appendix-c-poc-environment.md

## Observations

1. Appendix C makes the skill write apply-ready Terraform and a deploy script when `POC_ENVIRONMENT.md` is present, which reverses the "infra owner completes §10" stance for that case. Is a conditional appendix the right shape, or should Enterspeed-specific deployment live in its own skill?
2. The Terraform was validated (`fmt`, `validate`, and a read-only `plan` against the BRIM PoC environment) but planned as an Owner, not through the PoC PIM group, so the RBAC condition on role assignments is only exercised at a real `apply`. Fine to ship on that, or hold until the first real deploy?
3. A database (Appendix B) in the PoC environment is left as a `# TODO:` in C.2. Intended for v0, or should the first PoC with a database drive that addition?
