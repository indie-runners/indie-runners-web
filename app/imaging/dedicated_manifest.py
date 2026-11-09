import json
from pathlib import Path

MANIFEST_PATH = Path(__file__).parent / "dedicated_manifest.json"
REQUIRED_FIELDS = (
    "event_slug",
    "title",
    "photographer_name",
    "photographer_url",
    "photo_url",
)


def validate_entry(entry: dict, index: int) -> None:
    for field in REQUIRED_FIELDS:
        if field not in entry:
            raise ValueError(
                f"dedicated manifest entry {index} is missing field: {field}"
            )


def load_manifest(path: Path | str | None = None) -> list[dict]:
    p = Path(path) if path else MANIFEST_PATH
    if not p.exists():
        return []
    with p.open() as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("dedicated manifest root must be a JSON list")
    for i, entry in enumerate(data):
        validate_entry(entry, i)
    return data
