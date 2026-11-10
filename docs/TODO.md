# TODO: W-115 (#15) — Starting an Unsplash round is still done by hand: shortlist, queries, file

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-10_

- [ ] `.claude/skills/unsplash-round/SKILL.md`: candidates -> agreed list in chat -> `imports/` file -> print `unsplash_round.sh` command
- [ ] Never runs `unsplash_fetch.py` / `unsplash_round.sh` (input() EOFs under Bash, skips every event, exit 0)
- [ ] Max 25 events per file, split beyond; says why (50 req/h)
- [ ] Says the round is the one DB session across both repos
- [ ] Measure (Paulo): does `! <command>` give the pick a stdin? One-event file
- [ ] Real run: shortlist, agreed list, file, W-104 run on it (Paulo)
- [ ] IMAGING note, FILE_TREE line, CHANGELOG 1.9.78
- Unsure: the format target is `unsplash_round.sh`, not bare `unsplash_fetch.py`; `!` may have no TTY
