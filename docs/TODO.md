# TODO: W-111 — Nothing stops a private term from being committed to a public repo

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-09_

## Steps
- [x] `.githooks/` pre-commit + commit-msg, one shared `denylist.sh`
- [x] Term file `exports/private-terms.txt` in the main checkout, seeded
- [x] Seed terms checked against every `core.*` slug column (evidence W-111)
- [x] Proven both ways from the worktree (evidence W-111)
- [x] ARCHITECTURE § Local development, CHANGELOG, FILE_TREE

## Measure
- Refused / passed per case: done, see CHANGELOG 1.9.74.

## Unsure / disproved
- `core.hooksPath` is set in the shared config already. Until this merges,
  the main checkout has no `.githooks/`, and git skips the hooks there
  without a word.
- Speed on a very large diff: not measured. It's a single awk pass.
