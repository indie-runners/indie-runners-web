# TODO: W-115 (#15) — Starting an Unsplash round is still done by hand: shortlist, queries, file

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-10_

- [x] `.claude/skills/unsplash-round/SKILL.md`: candidates -> agreed list in chat -> `imports/` file -> print `unsplash_round.sh` command
- [x] Never runs `unsplash_fetch.py` / `unsplash_round.sh` (input() EOFs under Bash, skips every event, exit 0)
- [x] Max 25 events per file, split beyond; says why (50 req/h)
- [x] Says the round is the one DB session across both repos
- [x] Measure (Paulo): does `! <command>` give the pick a stdin? One-event file
- [x] Real run: shortlist, agreed list, file, W-104 run on it (Paulo)
- [x] IMAGING note, FILE_TREE line, CHANGELOG 1.9.78
- Disproved: `!` gives the pick a stdin (it EOFs). Measured: round of 15 -> 10 picked, all 10 credits live
