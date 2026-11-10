# Tile image pipeline

Operational reference for the offline image pipeline that produces the tile
images shown on the race grid. Covers the CLI, the bucket, and the day-to-day
procedures for adding a photo or bumping a version.

The runtime service design (auth, DB, sessions, deploy) lives in
`docs/ARCHITECTURE.md`. This file is purely about the offline `app/imaging/`
package plus the pure resolver that maps an event to a tile url.

## Overview

Two kinds of tile images:

- **Dedicated** — one hand-picked photo per event. Row in `web.event_images`
  marks the event as dedicated. Filename is `{event_slug}.jpg`.
- **Stock** — a small library of landscape photos bucketed by terrain
  (`trail`, `road`, `mixed`). Every non-dedicated event is deterministically
  hashed to one stock tile in its terrain bucket.

Resolver (`app/imaging/resolver.py`) is a pure function. It reads the
manifest and the dedicated lookup set, computes a stable md5-based index for
stock hits, and returns a public GCS url. Nothing in `app/imaging/` is
imported by the request path except `resolver.py`, and even that is not
wired into any route yet.

Everything else (`stylers.py`, `publish.py`, `stock_manifest.py`,
`dedicated_manifest.py`, `__main__.py`, `scripts/generate_stock_manifest.py`,
`scripts/generate_dedicated_manifest.py`) is offline batch tooling that runs
from a workstation.

## Photographer credits

Every stock and dedicated tile is credited on the event page hero via a
small pill (`Photo by {name} on Unsplash` with two Unsplash-license
links). Credit data lives in three columns on `web.event_images`:
`attribution_name`, `attribution_url` (photographer profile), and
`attribution_source_url` (photo page). All three are nullable; the
template gracefully degrades to a plain-text `Photo · {name}` when the
URLs are missing, and to nothing when the name is missing.

The columns are populated from two JSON manifests, checked in:

- `app/imaging/stock_manifest.json` — one entry per stock slot. Generated
  from `docs/stock_credits.md` via `scripts/generate_stock_manifest.py`.
- `app/imaging/dedicated_manifest.json` — one entry per dedicated event
  slug. Generated from `docs/dedicated_credits.md` via
  `scripts/generate_dedicated_manifest.py`.

Runtime maintenance is automatic:

- **New event with a stock tile:** `EventImageService.get_or_create_for_events`
  reads the stock manifest at insert time and populates all three
  attribution columns alongside the `stock_filename` — no follow-up
  script needed.
- **New dedicated event:** on app startup, right after the dedicated
  slug cache is loaded from GCS, `EventImageService.refresh_dedicated_attributions`
  walks every row whose `event_slug` is dedicated and (re)writes the
  three columns from the dedicated manifest. Idempotent — a no-op after
  the first restart following the manifest change.
- **One-shot backfill of existing rows** (for the initial rollout, or
  after wide manifest edits): `python scripts/backfill_event_image_attribution.py`.
  Idempotent, prints per-source counts, exits non-zero on any un-matched
  row.

## Bucket layout

Public bucket, europe-west1, Uniform access, `allUsers` = Storage Object Viewer.

```
gs://indie-runners-web-tiles/
  originals/
    dedicated/{event_slug}.jpg
    stock/{filename}.jpg
  tiles/
    v01/
      dedicated/{event_slug}.webp
      stock/{filename}.webp
    v02/
      ...
    v03/
      ...
```

- `originals/` is never versioned. Same source bytes drive every version.
- `tiles/vNN/` is the styler pipeline version, not a manifest of images.
  Bump only when the styler settings change or the styler class changes.
  Adding or removing a photo does not require a new version.

Public url pattern:

```
https://storage.googleapis.com/indie-runners-web-tiles/tiles/{version}/{dedicated|stock}/{filename}.webp
```

## Local layout

```
app/imaging/
  __init__.py
  stylers.py                ImageStyler base, DuotoneStyler, ColorGradeStyler, PassthroughStyler
  publish.py                publish_image, publish_all — GCS upload plus outputs/ mirror
  stock_manifest.py         load_manifest, validate_entry
  dedicated_manifest.py     load_manifest, validate_entry
  resolver.py               resolve_tile_image (pure, no IO)
  __main__.py               CLI entry: python -m app.imaging
  stock_manifest.json       generated; checked into the repo
  dedicated_manifest.json   generated; checked into the repo
  inputs/
    dedicated/              drop dedicated originals here; gitignored
    stock/                  drop stock originals here; gitignored
  outputs/                  local mirror of everything published; gitignored
```

Credits docs:

- `docs/stock_credits.md` — one `## {terrain}_{NN} — Title` heading per
  stock image plus a `Photo by <a>Name</a> on <a>Unsplash</a>` line.
  Source of truth for `stock_manifest.json`.
- `docs/dedicated_credits.md` — one `## {event_slug} — Title` heading
  per dedicated photo plus the same Unsplash credit line. Source of
  truth for `dedicated_manifest.json`.

Manifest generators:

- `scripts/generate_stock_manifest.py`
- `scripts/generate_dedicated_manifest.py`

## CLI reference

```
python -m app.imaging --style {duotone,grade,passthrough}
                     [--tile-version vNN]
                     [--shadow #RRGGBB] [--mid #RRGGBB] [--highlight #RRGGBB]
                     [--duotone-config path.json]
```

Arguments:

- `--style` (required)
  - `duotone` — grayscale then colorize with forest green shadow, mid, and
    off-white highlight. Site default.
  - `grade` — light desaturation, small contrast lift, forest-green wash at
    10 percent strength.
  - `passthrough` — resize only. Untouched color baseline for comparisons.
- `--tile-version` (optional; defaults to `publish.TILE_VERSION`, currently
  `v01`) — target prefix under `tiles/`. Set this when publishing a new
  version alongside the existing ones. Example:
  `python -m app.imaging --style grade --tile-version v03`.
- `--shadow`, `--mid`, `--highlight` (optional; `--style duotone` only) —
  override the duotone palette globally as `#RRGGBB` (or `RRGGBB`).
  Applies to every file in the batch. Ignored for `grade` and
  `passthrough`.
- `--duotone-config` (optional; `--style duotone` only) — JSON file
  mapping terrain → per-component hex triple. Example:
  ```json
  {
    "trail": {"shadow": "#0f2010", "mid": "#2d4430", "highlight": "#e8f0e0"},
    "road":  {"shadow": "#1a1a1e", "mid": "#3a3f45", "highlight": "#e0e0e5"},
    "mixed": {"shadow": "#1a2010", "mid": "#3a4a2a", "highlight": "#e8ede0"}
  }
  ```
  Precedence per file: `config[terrain][component]` → global flag →
  `DuotoneStyler` class default. Missing terrains fall through to the
  global flags. Dedicated files follow the same rules as stock — their
  `{terrain}_` filename prefix picks the palette.

Behaviour:

- Walks `app/imaging/inputs/dedicated/` and `app/imaging/inputs/stock/`.
- For each file: uploads the untouched original to
  `originals/{kind}/{filename}.jpg`, runs the styler, encodes WebP at
  quality 82, uploads to `tiles/{version}/{kind}/{stem}.webp`, and mirrors
  both to `app/imaging/outputs/`.
- Prints one plain `publishing <filename>` line per file. No exclamation
  marks anywhere.
- Idempotent: reruns overwrite blobs with the same bytes (when the styler
  and inputs are unchanged).

Manifest generator:

```
python scripts/generate_stock_manifest.py
```

Parses `docs/stock_credits.md`, cross-references with the filenames in
`app/imaging/inputs/stock/` by the `{terrain}_{NN}` prefix, writes
`app/imaging/stock_manifest.json`. Aborts with a plain warning listing
mismatched keys if any credit entry lacks a file or vice versa. Does not
overwrite the manifest on abort.

## Adding a stock photo

1. Rename the file to the convention:
   `{terrain}_{NN}_{slug}-{photographer-handle}-{unsplash-photo-id}-unsplash.jpg`.
   - Terrain: `trail`, `road`, or `mixed`.
   - NN: next free two-digit slot in that bucket. Slots are per-terrain.
   - Slug: short kebab-case description. Prefer dashes over underscores for
     consistency with existing files.
   - Photographer handle: from the Unsplash profile url
     `unsplash.com/@handle`.
   - Photo id: trailing token before the query string in the Unsplash photo
     url.
2. Drop the file into `app/imaging/inputs/stock/`. Gitignored, stays local.
3. Add a credit entry to `docs/stock_credits.md` under the matching bucket
   heading (`# Trail`, `# Road`, `# Mixed`):
   ```markdown
   ## mixed_05 — Lakeside boardwalk

   Photo by <a href="https://unsplash.com/@handle?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Photographer Name</a> on <a href="https://unsplash.com/photos/slug-photoId?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>
   ```
   The Unsplash download popup ships this html — copy it in.
4. Regenerate the manifest:
   ```
   python scripts/generate_stock_manifest.py
   ```
   Expected: `wrote app/imaging/stock_manifest.json with N entries`. On
   mismatch it lists the offending keys and exits 1. Any new event that
   later hashes into the updated slot will pick up its photographer
   credit automatically at insert time. Existing events already
   assigned to the same slot keep their previous credit (their row is
   not rewritten) — rerun the backfill script if you want to sweep
   them:
   ```
   python scripts/backfill_event_image_attribution.py
   ```
5. Publish the live version so the new tile exists on the served path.
   Only `v02` (passthrough) is currently rendered — `app/config.py` sets
   `tile_version = "v02"` and `scripts/deploy.sh` does not override it,
   so any other prefix in the bucket is unreachable from the site:
   ```
   python -m app.imaging --style passthrough --tile-version v02
   ```
   Existing files are re-uploaded with identical bytes. Wasted bandwidth
   but harmless. If a comparison against a retired styler is needed,
   publish that styler under a fresh version prefix and flip
   `TILE_VERSION` temporarily (see *Publishing a new version* below).
6. Verify:
   ```
   curl -sI "https://storage.googleapis.com/indie-runners-web-tiles/tiles/v02/stock/mixed_05_lakeside-boardwalk-handle-photoId-unsplash.webp" | head -3
   ```
   Expect `HTTP/2 200` and `content-type: image/webp`.
7. Commit `docs/stock_credits.md` and `app/imaging/stock_manifest.json`.
   Never commit `app/imaging/inputs/` (gitignored anyway).

Warning: adding one entry to a terrain bucket shifts which event maps to
which stock file for the events that were already hashing into that bucket.
The modulus in `resolver.py` is `len(bucket_entries)`, so roughly `1/N` of
events in that terrain will swap tiles. Cosmetic, but expected.

## Sourcing photos from the Unsplash API

`scripts/unsplash_fetch.py` automates everything around the one step worth
keeping manual — choosing a photo that looks like the event. It searches,
shows candidates, and on your pick triggers the Unsplash download endpoint,
downloads the original, writes the credit entry, regenerates the manifest
and publishes.

Setup, once: register an app at <https://unsplash.com/oauth/applications>
and put the Access Key in `.env` as `UNSPLASH_ACCESS_KEY`. The demo tier
(50 requests/hour) is enough — each event costs one search plus one
download trigger, so roughly 25 events per hour. The key authenticates the
*application*, not a user account: `GET /me` returns 401, and results
therefore cannot vary by Unsplash account tier.

Unsplash+ (paid licence) content is excluded server-side by the public
search endpoint — verified across 120 results on four queries, none
carrying a paid marker under any spelling. The script still filters and
prints a count rather than dropping silently, so a change in that
behaviour would be visible rather than quietly polluting the library.

Which events to work on: `scripts/photo_candidates.py` prints a ranked
shortlist of events that still use a stock tile, ordered by engagement
then by how many other events share their stock file, and flags events
with no location (which cannot be searched). Events that already have a
dedicated photo are excluded — they are finished work.

```
python scripts/photo_candidates.py --limit 30
python scripts/photo_candidates.py --by-collision --country Germany
```

The batch pattern. `publish_all` walks every file under `inputs/`, so
publishing once per photo re-uploads the whole library each time. Fetch
with `--no-publish`, then publish the batch:

```
python scripts/unsplash_fetch.py budapest_half_marathon --no-publish
python scripts/unsplash_fetch.py stockholm_marathon     --no-publish
...
python scripts/generate_dedicated_manifest.py
python -m app.imaging --style passthrough --tile-version v02
```

Then **restart the app** and run `python scripts/backfill_event_image_attribution.py`.
The restart reloads the dedicated slugs, but the serving image's baked
manifest predates the round, so only the backfill writes the new credits.

`bash scripts/unsplash_round.sh <file>` does all of the above from a file of
`<slug> [query]` lines: the picks stay interactive, the restart asks for `y`,
and it says so if the backfill did not run. It is a DB-touching session.
`/unsplash-round` (Claude Code) prepares that file: it runs the shortlist,
agrees a query per event in chat, and prints the command. The picks stay in
your own terminal; Claude Code's `!` gives them no stdin.

Trail events need `--query` almost every time. The tile location is a
trailhead village, and villages are not photographed: `Malaucène` returns
0 results, `Ochotnica Dolna` returns 1. The massif the race crosses is
what runners recognise and what Unsplash has — `Mont Ventoux` returns 16,
`Gorce Poland` 7. City races generally work off the tile location as-is.

```
python scripts/unsplash_fetch.py grand_raid_ventoux --no-publish --query "Mont Ventoux"
```

`--terrain {trail,road,mixed}` sets the `{terrain}_` filename prefix
(default `mixed`). The prefix is stripped before upload and only selects a
duotone palette, so while the site publishes `passthrough` it has no
effect on output — set it for accuracy, not because anything breaks.

The script refuses events that already have a dedicated photo, and exits
with an explanation for events whose tile shows no location. Skipping is a
first-class outcome: `s` at the prompt leaves the event on stock, which is
what stock is for.

Credit entries it writes carry `utm_source=indie_runners` per the API
guidelines, rather than the `utm_source=unsplash` that the website's
download popup ships. Both forms are valid and both parse — entries added
by hand before this script existed were not rewritten.

### Where the conversion effort stopped, and why

166 of 246 events carry a dedicated photo. The remaining ~80 were left on
stock deliberately, and the reasons are worth knowing before anyone
restarts the grind:

- **No `race_location`** (12 events). Nothing to search. `unsplash_fetch.py`
  refuses these with an explanation rather than guessing.
- **Location shared with another remaining event** (13 events — six more
  "Berlin", three "London", two each "Warszawa" and "Paris"). The searches
  return landmarks already used on other tiles. Two near-identical hero
  images look like a bug; one shared stock photo does not. If these are ever
  done, query by district (`Tegeler Forst`, `Müggelsee`, `Tempelhofer Feld`)
  rather than the city.
- **Small local races in unphotographed places** — Rägelin, Zehdenick,
  Kopřivnice, Běchovice, Winschoten, Bräunlingen. Unsplash has little or
  nothing, so `s` (skip) is the correct answer.
- **Unusable location strings** that need a hand-written query:
  `berlin_campus_run` ("mitten auf und rund um den Campus"),
  `muddy_angel_run` ("Mitten in Deutschland"), `camino_de_dragones`,
  `run_spirit`, `vodno_matka_trails`.

This is the intended end state, not an unfinished job. Stock is the
fallback for events with no usable location and events with no suitable
photo — which is why the thin `mixed` bucket was left at 11 files rather
than grown: conversions shrink the population stock has to cover.

`python scripts/photo_candidates.py` remains the way to see what is left;
newly scraped events will appear there as they arrive.

## Adding a dedicated photo

1. Rename the file to `{terrain}_{event_slug}.jpg` and drop it into
   `app/imaging/inputs/dedicated/`. The slug must match
   `core.events.event_slug` for the event you are marking as dedicated.
   The `{terrain}_` prefix (`trail`, `road`, or `mixed`) tells the
   publish CLI which duotone palette to apply when a `--duotone-config`
   is passed; the prefix is stripped before upload so the bucket path
   stays `dedicated/{event_slug}.webp` and the resolver keeps working.
   Publish fails loud if the prefix is missing or is not one of the
   three terrains.
2. Add a credit entry to `docs/dedicated_credits.md`:
   ```markdown
   ## <event_slug> — Human-readable title

   Photo by <a href="https://unsplash.com/@handle?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Photographer Name</a> on <a href="https://unsplash.com/photos/slug-photoId?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>
   ```
3. Regenerate the dedicated manifest:
   ```
   python scripts/generate_dedicated_manifest.py
   ```
   Expected: `wrote app/imaging/dedicated_manifest.json with N entries`.
   Aborts and exits 1 on mismatch between file and credit entry.
4. Publish the live version. Only `v02` (passthrough) is currently
   rendered — see the note under *Adding a stock photo* step 5:
   ```
   python -m app.imaging --style passthrough --tile-version v02
   ```
5. Restart the app (locally: Ctrl-C and rerun `uvicorn`; production:
   `gcloud run deploy` or a service restart). Startup does two things:
   loads the dedicated slug cache from GCS so the resolver serves the
   dedicated tile, and calls
   `EventImageService.refresh_dedicated_attributions` to (re)write the
   three attribution columns for any row now identified as dedicated.

   **This step is not optional, and skipping it silently credits the wrong
   photographer.** The image resolves by slug as soon as the blob exists,
   but the credit pill reads `web.event_images`, which only the startup
   hook rewrites. In between, the tile shows the new photo with the old
   stock photographer's name and profile link — nothing errors, nothing
   looks broken, and the link resolves to a real person who did not take
   that picture. Verify after restarting:

   ```
   python -c "
   import sys; sys.path.insert(0,'.')
   from sqlalchemy import text
   from app.db import SessionLocal
   db=SessionLocal()
   print(db.execute(text(\"SELECT attribution_name FROM web.event_images WHERE event_slug='<slug>'\")).scalar())
   db.close()"
   ```

   The startup refresh only covers slugs in the serving image's baked
   manifest. A photo published since that image was built needs
   `python scripts/backfill_event_image_attribution.py`, which writes the
   columns directly from the manifests.
6. Verify the public url resolves, the tile renders on the site, and
   the credit pill shows the new photographer.

No manual database write is required. Presence of
`originals/dedicated/{event_slug}.jpg` in the bucket is the flag; the
startup refresh writes attribution to the matching row.
`web.event_images.kind` is not consulted for dedicated resolution —
the column still exists for future use.

## Publishing a new version

Bump `vNN` when the styler settings change (colors, contrast, saturation)
or you switch styler class. Do not bump for adding photos.

1. Change the styler class or its constants in `app/imaging/stylers.py`.
   Or create a new styler class if it needs new logic.
2. Register the new styler in `app/imaging/__main__.py` under `STYLERS`
   (if it is a new class).
3. Publish under a fresh version prefix:
   ```
   python -m app.imaging --style <name> --tile-version v04
   ```
4. Flip the site to the new version. Two paths:

   - **Temporary** (test a version live without a deploy): set the env
     var on Cloud Run directly. This overrides the code default until a
     later deploy resets it.
     ```
     gcloud run services update indie-runners-web \
         --region europe-west1 \
         --update-env-vars TILE_VERSION=v04
     ```
   - **Permanent**: edit `tile_version` in `app/config.py`, commit,
     redeploy. Any deploy after this always ships this version unless
     the Cloud Run env var is set to override.

   Rollback: reverse either step.

Old prefixes stay in the bucket for free rollback until you delete them.

### Side-by-side comparison workflow

Only the live version is published as part of the day-to-day add-a-photo
flow. When evaluating a candidate styler against the current one, publish
the alternative under a fresh version prefix — the live version stays
served meanwhile:

```
python -m app.imaging --style passthrough --tile-version v02   # currently live
python -m app.imaging --style grade       --tile-version v03   # candidate
```

Each has its own path in the bucket. Flip `TILE_VERSION` (env var on
Cloud Run, or `app/config.py` default) between viewings to compare in
context. Both URLs are independently reachable — a static HTML compare
page can stitch them without touching the app.

## Bucket and ADC setup

Bucket `indie-runners-web-tiles`:

- Region: europe-west1 (matches Cloud Run).
- Storage class: Standard.
- Access control: Uniform.
- Public access prevention: off.
- Principals:
  - `allUsers` — Storage Object Viewer (public reads for tile URLs).
  - Local publish runs under the operator's own gcloud account. The web
    service account holds no storage role; grants are declared in
    `indie-runners-infra/web/tiles.tf`.

Application Default Credentials for local publish:

```
gcloud auth application-default login
gcloud auth application-default set-quota-project indie-runners-dev-470411
```

Verify:

```
gcloud auth application-default print-access-token >/dev/null && echo ok
```

`google-cloud-storage` picks up ADC automatically. No auth code in
`publish.py`. If credentials are missing the SDK raises with a clear error.

## Deleting stale versions

Free to delete once you have committed to a newer version and confirmed it
in production for long enough that you would not roll back.

UI: Cloud Storage → Buckets → `indie-runners-web-tiles` → find the
`tiles/vNN/` prefix, select all objects under it, delete.

CLI:

```
gcloud storage rm --recursive gs://indie-runners-web-tiles/tiles/vNN/
```

Do not delete anything under `originals/`. That's the source of truth for
re-deriving any tile version.
