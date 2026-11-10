# TODO: W-104 — An Unsplash round is five commands, and the one that sets the credits is easy to miss

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-10_

## Steps
- [x] `scripts/unsplash_round.sh`: fetch per line, manifest, publish, restart (asks y), backfill
- [x] Dry run on stubs: parsing, tty stdin for the pick, stop-on-failure, decline, full path
- [x] IMAGING batch pattern, FILE_TREE, CHANGELOG
- [ ] Acceptance 5, a real round: Paulo, after W-115

## Unsure / disproved
- The fetch also opens a DB session (it reads the index), not only the
  backfill. The header says the whole run is the session.
- If traffic is pinned to an old revision (W-068), the restart's new
  revision gets no traffic; the second `--check` would show the old name.
