---
name: unsplash-round
description: Start an Unsplash photo round — shortlist events, agree a search query per event in chat, write the round file, print the command Paulo runs to pick. Paulo's own command.
disable-model-invocation: true
---

# Start an Unsplash round

Prepares a round for `scripts/unsplash_round.sh` (W-104). You shortlist and
write the file; Paulo picks the photos in his own terminal.
`docs/IMAGING.md` § "Sourcing photos from the Unsplash API" is the background.

**Never run `unsplash_round.sh` or `unsplash_fetch.py` yourself.** The pick is
`input()`, which gets `EOFError` under the Bash tool; the fetch turns that
into a skip, so every event would be skipped, the search requests spent,
and the run would still exit 0.

## 1. Database first

Say this before running anything: the shortlist reads the database, and the
round itself does too (the fetch reads the index, the backfill writes
`web.event_images`). That makes this the **one DB-touching session across
both repos** — ask Paulo whether anything else is running in either repo.
The Cloud SQL proxy must be up (`scripts/db_proxy.sh`, port 5432).

## 2. Shortlist

From the repo root, passing through what Paulo asked for:

```bash
python scripts/photo_candidates.py [--limit N] [--country <name>] [--by-collision]
```

Show the list. For each event, propose a query, starting from the location
the script prints (it is the string the tile renders):

- **City race:** the location as-is usually works; leave the query empty.
- **Trail event** (terrain `trail`, or a village location): flag it and
  propose the massif, range or landmark instead. Villages return nothing
  (`Malaucène` 0 results, `Mont Ventoux` 16).
- **`NO LOCATION — cannot search`:** flag it; it needs a hand-written
  query or must be left off. Without a query the fetch exits 1 and the
  round stops at that line.
- A location another remaining event shares (Berlin, London…): flag it;
  query a district, or leave it off.

Paulo agrees, edits or drops lines in chat. Do not write the file until he
agrees.

## 3. Write the file

At most **25 events per file**. The Unsplash demo tier allows 50 requests an
hour, one search and one download per event, and every `m` (more results)
costs another search. Over 25, split into `_1`, `_2`… files and say to run
them at least an hour apart.

The round writes the manifest and credits into the checkout that runs it, so
run it in the main checkout (first line of `git worktree list`) on a fresh
branch (`git checkout -b round/<date>`), never in a ticket worktree. Write the
file to that checkout's `imports/` (gitignored; `mkdir -p` it), named
`unsplash_round_<YYYY-MM-DD>.txt`, one event per line, exactly the format
`unsplash_round.sh` reads:

```
<slug>
<slug> <query, may contain spaces>
```

No quotes around the query. Print the absolute path.

## 4. Hand over

Print, for Paulo's own terminal, from the repo root:

```bash
bash scripts/unsplash_round.sh imports/unsplash_round_<date>.txt
```

Say what it will do: one interactive pick per event, then manifest, publish,
a production restart that asks for `y`, and the backfill that sets the
credits. Then commit `docs/dedicated_credits.md` and
`app/imaging/dedicated_manifest.json` through a PR.
