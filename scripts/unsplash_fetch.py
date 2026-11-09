"""Search Unsplash for an event's location and wire up a dedicated photo.

Converts stock events to dedicated, one at a time. The aesthetic judgement
stays manual — the script searches, shows candidates, and on your pick does
every mechanical step around it:

  1. searches Unsplash for the location the tile renders, landscape only
  2. writes a local HTML contact sheet and opens it
  3. on pick: triggers the Unsplash download endpoint (required by the API
     guidelines — it credits the photographer's download stats)
  4. downloads the full-res original to inputs/dedicated/{terrain}_{slug}.jpg
  5. appends a credit entry to docs/dedicated_credits.md in the exact shape
     scripts/generate_dedicated_manifest.py parses
  6. regenerates the manifest and publishes to GCS

Events that already have a dedicated photo are refused: they are finished
work. Stock stays as the fallback for events with no usable location and
for events where nothing in the search fits — skipping is a first-class
outcome here, not a failure.

web.event_images rows are deliberately left alone. A dedicated event keeps
its stale stock_filename, which resolver.py never reads (it resolves
dedicated by slug). That matches how the existing 13 dedicated events
already behave; changing DB semantics inside a photo-fetch script would be
a surprise. See docs/ARCHITECTURE.md, Static assets.

Requires UNSPLASH_ACCESS_KEY in the environment or .env. Register an app at
https://unsplash.com/oauth/applications — the demo tier (50 requests/hour)
is enough; each event costs one search plus one download trigger.

Usage:
    python scripts/unsplash_fetch.py <event_slug> [--query "..."] [--terrain trail]
    python scripts/unsplash_fetch.py <event_slug> --no-publish
"""

from __future__ import annotations

import argparse
import os
import sys
import webbrowser
from html import escape
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import httpx

from app.config import settings
from app.db import SessionLocal
from app.imaging.dedicated_index import load_dedicated_slugs
from app.services.race_service import RaceFilters, RaceService

API_ROOT = "https://api.unsplash.com"
# Sent as utm_source on attribution links, per the API guidelines. The docs'
# existing entries carry utm_source=unsplash because they were copied from the
# website's download popup; new entries identify this app instead.
APP_NAME = "indie_runners"
UTM = f"utm_source={APP_NAME}&utm_medium=referral&utm_content=creditCopyText"

CREDITS_PATH = REPO_ROOT / "docs" / "dedicated_credits.md"
DEDICATED_DIR = REPO_ROOT / "app" / "imaging" / "inputs" / "dedicated"
CONTACT_SHEET = REPO_ROOT / "app" / "imaging" / "outputs" / "_contact_sheet.html"

TERRAIN_BUCKETS = ("trail", "road", "mixed")
PER_PAGE = 12
# The publish CLI reads the {terrain}_ prefix to pick a duotone palette. The
# site publishes passthrough today, so the prefix is inert — but it must be
# present and valid or publish_image raises.
DEFAULT_TERRAIN = "mixed"


def search_photos(client: httpx.Client, query: str, page: int) -> list[dict]:
    r = client.get(
        f"{API_ROOT}/search/photos",
        params={
            "query": query,
            "orientation": "landscape",
            "per_page": PER_PAGE,
            "page": page,
            "content_filter": "high",
        },
    )
    r.raise_for_status()
    results = r.json().get("results", [])

    # Unsplash+ carries a paid licence this pipeline cannot rely on. The
    # public search endpoint appears to exclude it server-side already —
    # probing 60 results across two queries turned up no paid marker under
    # any spelling, and asset_type was uniformly 'photo'. This filter is
    # therefore a belt-and-braces check, not the primary control: it prints
    # rather than dropping silently, so if paid results ever do appear the
    # count is visible instead of the library quietly acquiring one.
    free, paid = [], []
    for p in results:
        if any(p.get(k) for k in ("premium", "plus", "plus_only")):
            paid.append(p)
        else:
            free.append(p)
    if paid:
        print(f"  dropped {len(paid)} Unsplash+ result(s) — paid licence")
    return free


def write_contact_sheet(query: str, photos: list[dict], path: Path) -> None:
    cards = []
    for i, p in enumerate(photos, start=1):
        desc = p.get("description") or p.get("alt_description") or ""
        cards.append(
            f"""
            <figure>
              <div class="n">{i}</div>
              <img src="{escape(p['urls']['small'])}" alt="{escape(desc)}">
              <figcaption>
                <strong>{escape(desc[:90] or 'no description')}</strong><br>
                {escape(p['user']['name'])}
                (<a href="{escape(p['links']['html'])}" target="_blank">view</a>)
              </figcaption>
            </figure>
            """
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"""<!doctype html>
<meta charset="utf-8">
<title>Unsplash candidates — {escape(query)}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #faf9f6; }}
  h1 {{ font-size: 1.1rem; font-weight: 600; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.2rem; }}
  figure {{ margin: 0; background: #fff; border-radius: 8px; overflow: hidden;
            box-shadow: 0 1px 4px rgba(0,0,0,.12); position: relative; }}
  img {{ width: 100%; height: 180px; object-fit: cover; display: block; }}
  .n {{ position: absolute; top: 8px; left: 8px; background: #2d4430; color: #fff;
        width: 26px; height: 26px; border-radius: 13px; display: grid;
        place-items: center; font-size: .85rem; font-weight: 600; }}
  figcaption {{ padding: .6rem .7rem; font-size: .8rem; line-height: 1.4; color: #333; }}
  a {{ color: #2d4430; }}
</style>
<h1>Query: {escape(query)} — type the number back in the terminal, or s to skip</h1>
<div class="grid">{''.join(cards)}</div>
""")


def trigger_download(client: httpx.Client, photo: dict) -> None:
    """Required by the Unsplash API guidelines whenever a photo is used."""
    location = photo.get("links", {}).get("download_location")
    if not location:
        print("  warning: no download_location on this photo, skipping the trigger")
        return
    r = client.get(location)
    r.raise_for_status()


def download_original(photo: dict, dest: Path) -> None:
    # urls.full is the maximum-dimension jpg. urls.raw is only a base URL
    # needing sizing params, so it is the wrong one to pull. No auth header —
    # this is the image CDN, and image requests do not count against the
    # API rate limit.
    url = photo["urls"]["full"]
    with httpx.stream("GET", url, timeout=60.0, follow_redirects=True) as r:
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as fh:
            for chunk in r.iter_bytes():
                fh.write(chunk)


def credit_entry(slug: str, title: str, photo: dict) -> str:
    """Exactly the shape generate_dedicated_manifest.py's CREDIT_RE parses."""
    name = photo["user"]["name"]
    profile = f"https://unsplash.com/@{photo['user']['username']}?{UTM}"
    photo_url = f"{photo['links']['html']}?{UTM}"
    return (
        f"\n## {slug} — {title}\n\n"
        f'Photo by <a href="{profile}">{name}</a> '
        f'on <a href="{photo_url}">Unsplash</a>\n'
    )


def prompt(msg: str) -> str:
    try:
        return input(msg).strip()
    except EOFError:
        # Non-interactive stdin: treat as a skip rather than crashing, so a
        # piped run degrades instead of half-writing an entry.
        print("\nno input available, skipping")
        return "s"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("event_slug", help="event to give a dedicated photo")
    parser.add_argument(
        "--query",
        help="override the search query. Defaults to the location the tile "
             "renders, which is sometimes a street address and worth replacing.",
    )
    parser.add_argument(
        "--terrain",
        choices=TERRAIN_BUCKETS,
        default=DEFAULT_TERRAIN,
        help="filename prefix the publish CLI reads for its palette "
             "(default: %(default)s)",
    )
    parser.add_argument(
        "--no-publish",
        action="store_true",
        help="stop after writing the file and credit entry, so a batch can be "
             "published in one go later.",
    )
    args = parser.parse_args()

    # settings reads .env, which is where the key normally lives. A shell
    # export still wins, so a one-off key can be passed without editing .env.
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY") or settings.unsplash_access_key
    if not access_key:
        print("error: UNSPLASH_ACCESS_KEY is not set.")
        print("Register an app at https://unsplash.com/oauth/applications and")
        print("export the Access Key (demo tier, 50 req/hour, is enough).")
        return 1

    slug = args.event_slug

    dedicated = load_dedicated_slugs()
    if slug in dedicated:
        print(f"{slug} already has a dedicated photo. Leaving it alone.")
        return 0

    # The tile's location is the seed for the query, so the photo matches the
    # event as the site presents it. See scripts/photo_candidates.py.
    db = SessionLocal()
    try:
        tiles = {
            item.event_slug: item
            for item in RaceService(db).list_races(RaceFilters())
        }
    finally:
        db.close()

    tile = tiles.get(slug)
    if tile is None:
        print(f"error: {slug} is not an upcoming event on the index.")
        return 1

    query = args.query or tile.location
    if not query:
        print(f"{tile.name} has no location on its tile, so there is nothing to")
        print("search for. Pass --query to name the place yourself, or leave the")
        print("event on stock — that is what stock is for.")
        return 1

    print(f"event:    {tile.name}")
    print(f"location: {tile.location or '(none)'}")
    print(f"query:    {query}")
    print()

    headers = {
        "Authorization": f"Client-ID {access_key}",
        "Accept-Version": "v1",
    }
    with httpx.Client(headers=headers, timeout=30.0) as client:
        page = 1
        while True:
            try:
                photos = search_photos(client, query, page)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    print("error: rate limited or key rejected by Unsplash (403).")
                    print("The demo tier allows 50 requests/hour.")
                else:
                    print(f"error: Unsplash returned {e.response.status_code}")
                return 1

            if not photos:
                print(f"no usable results for {query!r}"
                      + (f" on page {page}" if page > 1 else ""))
                print("Leave it on stock, or retry with --query.")
                return 0

            write_contact_sheet(query, photos, CONTACT_SHEET)
            print(f"{len(photos)} candidates -> {CONTACT_SHEET}")
            webbrowser.open(CONTACT_SHEET.as_uri())

            choice = prompt("pick a number, m for more, or s to skip: ").lower()
            if choice == "s":
                print("skipped. The event keeps its stock photo.")
                return 0
            if choice == "m":
                page += 1
                continue
            if not choice.isdigit() or not (1 <= int(choice) <= len(photos)):
                print("not a valid choice, stopping without writing anything.")
                return 1

            photo = photos[int(choice) - 1]
            break

        title = prompt(f"short title for the credits doc [{tile.name}]: ") or tile.name

        # Trigger before downloading — the guidelines tie this to the download
        # itself, and doing it first means a failed trigger stops the write.
        trigger_download(client, photo)

    # publish.py strips the {terrain}_ prefix, so the bucket path stays
    # dedicated/{event_slug}.webp and the resolver keeps working.
    dest = DEDICATED_DIR / f"{args.terrain}_{slug}.jpg"
    if dest.exists():
        print(f"error: {dest.name} already exists. Remove it first to replace.")
        return 1

    print(f"downloading -> inputs/dedicated/{dest.name}")
    download_original(photo, dest)

    entry = credit_entry(slug, title, photo)
    with CREDITS_PATH.open("a") as fh:
        fh.write(entry)
    print(f"appended credit entry to {CREDITS_PATH.relative_to(REPO_ROOT)}")

    if args.no_publish:
        print()
        print("stopped before publishing. When the batch is done, run:")
        print("  python scripts/generate_dedicated_manifest.py")
        print("  python -m app.imaging --style passthrough --tile-version v02")
        print("then restart the app so it picks up the new dedicated slug.")
        return 0

    print()
    print("regenerating the dedicated manifest...")
    import subprocess

    gen = subprocess.run(
        [sys.executable, "scripts/generate_dedicated_manifest.py"],
        cwd=REPO_ROOT,
    )
    if gen.returncode != 0:
        print("manifest generation failed. The photo and credit entry are on")
        print("disk; fix the mismatch it reported, then rerun the generator.")
        return 1

    # publish_all walks every file under inputs/, so this re-uploads the whole
    # local library with identical bytes. Wasted bandwidth, not a correctness
    # problem — same tradeoff docs/IMAGING.md already accepts for add-a-photo.
    print("publishing to GCS...")
    pub = subprocess.run(
        [sys.executable, "-m", "app.imaging",
         "--style", "passthrough", "--tile-version", "v02"],
        cwd=REPO_ROOT,
    )
    if pub.returncode != 0:
        print("publish failed. Rerun the CLI directly once the cause is fixed.")
        return 1

    print()
    print(f"done. {slug} is dedicated.")
    print("Restart the app to refresh the dedicated slug cache and write the")
    print("attribution columns (docs/IMAGING.md, Adding a dedicated photo).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
