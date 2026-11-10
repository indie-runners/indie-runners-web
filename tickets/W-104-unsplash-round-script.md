# W-104 — An Unsplash round is five commands, and the one that sets the credits is easy to miss

`priority: 4` · `effort: S` · `area: tooling` · `deploy: none`
`source: docs/IDEAS.md 2026-11-03 (Paulo)`

## What is wrong

Paulo, from `docs/IDEAS.md`:

> include a script to do this in one whole bash script.

> Today a round is five manual steps after picking:
> `scripts/unsplash_fetch.py` per event with `--no-publish`, then
> `generate_dedicated_manifest.py`, `python -m app.imaging --style
> passthrough --tile-version v02`, a Cloud Run restart (redeploy the
> serving image by digest), and `backfill_event_image_attribution.py`.
> The last step is easy to miss: a restart alone leaves the new photos
> under the old stock credits, because the credit comes from the manifest
> baked into the running image (seen 2026-11-01).

Read at triage. A restart does not carry the new manifest: the serving
image was built before the round's manifest was committed, and startup
skips any dedicated slug its baked manifest lacks.

```
00086-nt2  created 2026-11-04T00:07:04Z, same digest as 00085 (AUDIT_20261104T0705)
fc73a9c    2026-11-04T00:07:35Z  app/imaging/dedicated_manifest.json +98 (round 5, 14 events)
app/services/event_image_service.py:223-225
            entry = _DEDICATED_BY_SLUG.get(row.event_slug)
            if entry is None:
                continue
```

So the restart reloads the dedicated slug cache from GCS (the new tiles
appear), and the backfill is what writes the credits. Neither alone is
the whole round.

## Acceptance

1. One bash script under `scripts/` takes a file of lines `<slug>
   [query]`, runs `unsplash_fetch.py --no-publish` for each (the photo
   pick stays interactive), then the manifest, the publish, the restart
   and the backfill, in that order. It stops at the first failing step
   and says which.
2. The restart is the production step. The script prints the serving
   revision before it (`deploy.sh --check`), asks for a `y` before
   creating a revision, and prints the new one after. It goes through
   the same path the round uses today, named in the script.
3. The backfill runs last and the script says so if it is skipped. It is
   the step that sets the credits.
4. The header comment says the backfill opens a DB session, so the
   one-session rule across both repos applies to the whole run.
5. Run once for a real round, or once on a one-event file. Paste the
   output, and a tile showing the new photo under its new credit.
6. `docs/IMAGING.md`'s batch pattern names the script; `FILE_TREE` lists it.

## Out of scope

- Choosing which events and queries go into a round
  (`photo_candidates.py` stays a separate, earlier step).
- Baking the manifest into a new image. That is a deploy, by
  `deploy.sh` or W-057's CD.
- Changing any of the four scripts it calls.

## Verdict

**VERDICT: BLOCKED — R1, R2** — 2026-11-10. Reasoning and docs are sound.
The PM ran a copy of the branch's script against stub `python`, `gcloud` and
`deploy.sh`, and two input paths break acceptance 1. R1: a last line with
no trailing newline is silently not fetched. R2: an unreadable (or empty)
list file doesn't stop the round, which runs manifest and publish and
reaches the restart prompt. Unblock: fix both, re-run those stubs, one
line in the changelog. No ROUTED_CHECKS entry (`deploy: none`).

**Not verified:** acceptance 5, a real round, was deferred by Paulo to
W-115, whose acceptance 8 runs this script on a real list. So the real
`gcloud run deploy --image <status.imageDigest>` restart, the backfill
and the tile credit check have not been run.
