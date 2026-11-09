import json
from pathlib import Path

MANIFEST_PATH = Path(__file__).parent / "stock_manifest.json"
REQUIRED_FIELDS = (
    "filename",
    "terrain",
    "slot",
    "title",
    "photographer_name",
    "photographer_url",
    "photo_url",
)
TERRAIN_BUCKETS = ("trail", "road", "mixed")


def validate_entry(entry: dict, index: int) -> None:
    for field in REQUIRED_FIELDS:
        if field not in entry:
            raise ValueError(f"stock manifest entry {index} is missing field: {field}")
    if entry["terrain"] not in TERRAIN_BUCKETS:
        raise ValueError(
            f"stock manifest entry {index} has invalid terrain: {entry['terrain']}"
        )


def load_manifest(path: Path | str | None = None) -> list[dict]:
    p = Path(path) if path else MANIFEST_PATH
    if not p.exists():
        raise FileNotFoundError(f"stock manifest not found at {p}")
    with p.open() as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("stock manifest root must be a JSON list")
    for i, entry in enumerate(data):
        validate_entry(entry, i)
    return data
