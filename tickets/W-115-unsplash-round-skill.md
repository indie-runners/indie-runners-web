# W-115 — Starting an Unsplash round is still done by hand: shortlist, queries, file

`priority: 2` · `effort: S` · `area: tooling` · `deploy: none`
`source: docs/IDEAS.md 2026-11-06 "A skill that starts an Unsplash photo round" (Paulo chose option A, 2026-11-10)`

## What is wrong

Paulo: *"create a skill to start the process of selecting photos in
unsplash, seemlessly."* Today a round starts by hand. You run
`scripts/photo_candidates.py` for the ranking, choose a query per event,
and type one `unsplash_fetch.py <slug> --no-publish` per event. W-104
automates everything after the pick, and its spec puts "choosing which
events and queries go into a round" out of scope. This ticket is that
earlier part. The two meet at W-104's input file.

## Evidence

- Six rounds from 2026-11-01 to 11-04 added 82 events, each started by
  hand (IDEAS entry, from those commit messages).
- `unsplash_fetch.py:181-183`: the pick is `input()`, and `prompt()`
  turns `EOFError` into a skip. Under Claude Code's Bash tool, `input()`
  raises `EOFError` (IDEAS entry, verified there). So a skill that calls
  the fetch script would skip every event, spend the search requests and
  exit 0.
- `docs/IMAGING.md` § "Sourcing photos from the Unsplash API": the demo
  tier allows 50 requests an hour, about 25 events. Trail events need
  `--query` "almost every time", because the tile location is a village
  nobody photographs.

## Acceptance (option A: the skill prepares, Paulo picks in his terminal)

1. A user-invocable skill, `.claude/skills/<name>/SKILL.md`. It's Paulo's
   own command, not a role skill, so it doesn't open with the roles
   README.
2. It runs `scripts/photo_candidates.py`, passing through what Paulo asks
   for (`--limit`, `--country`, `--by-collision`). It shows the shortlist
   and proposes a query per event, starting from the rendered location
   the script prints, and it flags trail events and events with no
   location. Paulo agrees or edits the list and the queries in chat.
3. It writes the agreed list to an **untracked** file (`imports/` or
   `exports/`, both gitignored), in exactly the `<slug> [query]` format
   W-104's script reads, and prints the path.
4. It never runs `unsplash_fetch.py` itself (see Evidence). It ends by
   printing the W-104 command for that file, for Paulo to run in his own
   terminal.
5. It refuses a list over 25 events, or splits it into files of up to 25,
   and it says why: the 50-request hourly limit, and each "m for more"
   costs another search.
6. It says the round opens DB sessions (candidates, then W-104's
   backfill), so the one-session rule across both repos applies.
7. **Settle the open question:** does Claude Code's `! <command>` prefix
   give the W-104 script a usable stdin for the pick? Try it once on a
   one-event file. If yes, step 4 offers `!` as well as a terminal. Either
   way, record the result in the changelog.
8. Run once for real: the shortlist, an agreed list, the file written,
   and W-104 run on it. A short note in `docs/IMAGING.md` names the
   skill, and `FILE_TREE` lists it.

## Sequence

**After W-104.** The file format belongs to W-104's script. Building the
skill first would mean guessing the format, and acceptance 4, 7 and 8
need the script to exist.

## Out of scope

- **Picking in chat (option B).** It needs a non-interactive flag on
  `unsplash_fetch.py`. Ticket it only if the change of window still
  bothers Paulo after this ships.
- **Changing any script.** `photo_candidates.py` and `unsplash_fetch.py`
  stay as they are, as in W-104.
- **Judging the photo.** The pick stays by eye, in the fetch script.

## Who builds it

`docs/roles/README.md` gives `.claude/skills/` to the chief of staff,
whose remit is the role machinery. This is a feature for Paulo rather
than role machinery. Default: the developer builds it under this ticket,
in one path under `.claude/skills/`, **if Paulo says so**. Otherwise it
goes to the chief of staff as written.
