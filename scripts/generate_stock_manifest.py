"""Parse docs/stock_credits.md and emit app/imaging/stock_manifest.json.

Matches credit entries to filenames in app/imaging/inputs/stock/ by the
{terrain}_{NN} prefix. Prints a plain warning and aborts if any credit entry
lacks a matching file or vice versa.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CREDITS_PATH = REPO_ROOT / "docs" / "stock_credits.md"
STOCK_DIR = REPO_ROOT / "app" / "imaging" / "inputs" / "stock"
MANIFEST_PATH = REPO_ROOT / "app" / "imaging" / "stock_manifest.json"

TERRAIN_BUCKETS = ("trail", "road", "mixed")

# Match a section heading like "## trail_01 — Alpine ridgeline (extra bits)".
# The dash is em (—) or en (–) or ascii hyphen; strip anything in parens off
# the title.
HEADING_RE = re.compile(
    r"^\s*##\s+(?P<key>(?:trail|road|mixed)_\d{2})\s*[—–-]\s*(?P<title>.+?)\s*$"
)
# Match one credit line (may span two source lines; we normalize whitespace
# before regex): 'Photo by <a href="...">Name</a> on <a href="...">Unsplash</a>'
CREDIT_RE = re.compile(
    r'Photo by\s+<a\s+href="(?P<photog_url>[^"]+)"[^>]*>(?P<photog_name>[^<]+)</a>'
    r'\s+on\s+<a\s+href="(?P<photo_url>[^"]+)"[^>]*>[^<]+</a>',
    re.IGNORECASE,
)


def parse_credits(path: Path) -> dict[str, dict]:
    """Return {key: {title, photographer_name, photographer_url, photo_url}}."""
    text = path.read_text()
    # Split on headings, keeping the heading with its body.
    lines = text.splitlines()
    entries: dict[str, dict] = {}
    current_key: str | None = None
    current_title: str | None = None
    current_body: list[str] = []

    def flush():
        if current_key is None:
            return
        # Normalize body whitespace so multi-line credit lines match.
        body = " ".join(l.strip() for l in current_body if l.strip())
        m = CREDIT_RE.search(body)
        if not m:
            raise ValueError(
                f"could not parse credit line for {current_key} in {path}"
            )
        entries[current_key] = {
            "title": current_title,
            "photographer_name": m.group("photog_name").strip(),
            "photographer_url": m.group("photog_url").strip(),
            "photo_url": m.group("photo_url").strip(),
        }

    for line in lines:
        h = HEADING_RE.match(line)
        if h:
            flush()
            current_key = h.group("key")
            current_title = h.group("title").strip()
            current_body = []
        else:
            if current_key is not None:
                current_body.append(line)
    flush()
    return entries


def scan_filenames(stock_dir: Path) -> dict[str, str]:
    """Return {key: filename_without_extension} for each stock jpg."""
    result: dict[str, str] = {}
    for path in sorted(stock_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() != ".jpg":
            continue
        stem = path.stem
        # key = terrain_NN prefix, e.g. 'trail_01'
        parts = stem.split("_", 2)
        if len(parts) < 2 or parts[0] not in TERRAIN_BUCKETS:
            print(f"warning, skipping file with unexpected name: {path.name}")
            continue
        key = f"{parts[0]}_{parts[1]}"
        if key in result:
            raise ValueError(
                f"duplicate key {key} in {stock_dir}: {result[key]} and {stem}"
            )
        result[key] = stem
    return result


def build_manifest(
    credits: dict[str, dict], filenames: dict[str, str]
) -> list[dict]:
    manifest = []
    for key in sorted(filenames):
        entry = credits[key]
        terrain, slot_str = key.split("_", 1)
        manifest.append(
            {
                "filename": filenames[key],
                "terrain": terrain,
                "slot": int(slot_str),
                "title": entry["title"],
                "photographer_name": entry["photographer_name"],
                "photographer_url": entry["photographer_url"],
                "photo_url": entry["photo_url"],
            }
        )
    return manifest


def main() -> int:
    if not CREDITS_PATH.exists():
        print(f"error, credits file not found: {CREDITS_PATH}")
        return 1
    if not STOCK_DIR.exists():
        print(f"error, stock inputs directory not found: {STOCK_DIR}")
        return 1

    credits = parse_credits(CREDITS_PATH)
    filenames = scan_filenames(STOCK_DIR)

    credit_keys = set(credits)
    file_keys = set(filenames)
    missing_files = sorted(credit_keys - file_keys)
    missing_credits = sorted(file_keys - credit_keys)

    if missing_files or missing_credits:
        print("mismatch between docs/stock_credits.md and inputs/stock/")
        if missing_files:
            print("credit entries with no matching file:")
            for k in missing_files:
                print(f"  {k}")
        if missing_credits:
            print("files with no matching credit entry:")
            for k in missing_credits:
                print(f"  {k} ({filenames[k]}.jpg)")
        print("stopping without writing manifest")
        return 1

    manifest = build_manifest(credits, filenames)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {MANIFEST_PATH.relative_to(REPO_ROOT)} with {len(manifest)} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
