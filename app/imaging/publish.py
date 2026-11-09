"""Upload originals and styler-derived tiles to GCS, mirror locally."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Callable, Iterable

from PIL import Image
from google.cloud import storage

from app.imaging.palette import terrain_from_filename
from app.imaging.stylers import ImageStyler

BUCKET_NAME = "indie-runners-web-tiles"
TILE_VERSION = "v01"
WEBP_QUALITY = 82

PACKAGE_ROOT = Path(__file__).resolve().parent
INPUTS_ROOT = PACKAGE_ROOT / "inputs"
OUTPUTS_ROOT = PACKAGE_ROOT / "outputs"
DEDICATED = "dedicated"
STOCK = "stock"

StylerFactory = Callable[[Path], ImageStyler]


def _kind_for(input_path: Path) -> str:
    parent = input_path.parent.name
    if parent not in (DEDICATED, STOCK):
        raise ValueError(f"input path must live under inputs/dedicated or inputs/stock: {input_path}")
    return parent


def _mirror_write(local_path: Path, data: bytes) -> None:
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(data)


def _gcs_stem(input_path: Path, kind: str) -> str:
    """For dedicated files, strip the {terrain}_ prefix from the on-disk name
    so the bucket path stays keyed by event_slug only (matches resolver URL)."""
    stem = input_path.stem
    if kind == DEDICATED and "_" in stem:
        return stem.split("_", 1)[1]
    return stem


def _gcs_filename(input_path: Path, kind: str) -> str:
    if kind == DEDICATED:
        return _gcs_stem(input_path, kind) + input_path.suffix
    return input_path.name


def publish_image(input_path: Path, styler_factory: StylerFactory, bucket) -> None:
    kind = _kind_for(input_path)
    filename = input_path.name

    if kind == DEDICATED:
        terrain_from_filename(input_path)  # raises on missing/invalid prefix

    print("publishing " + filename)

    original_bytes = input_path.read_bytes()
    remote_filename = _gcs_filename(input_path, kind)
    remote_stem = _gcs_stem(input_path, kind)

    original_gcs_path = f"originals/{kind}/{remote_filename}"
    bucket.blob(original_gcs_path).upload_from_string(
        original_bytes, content_type="image/jpeg"
    )
    _mirror_write(OUTPUTS_ROOT / "originals" / kind / remote_filename, original_bytes)

    styler = styler_factory(input_path)
    with Image.open(BytesIO(original_bytes)) as src:
        src.load()
        styled = styler.apply(src)

    buf = BytesIO()
    styled.save(buf, format="WEBP", quality=WEBP_QUALITY)
    webp_bytes = buf.getvalue()

    tile_gcs_path = f"tiles/{TILE_VERSION}/{kind}/{remote_stem}.webp"
    bucket.blob(tile_gcs_path).upload_from_string(
        webp_bytes, content_type="image/webp"
    )
    _mirror_write(
        OUTPUTS_ROOT / "tiles" / TILE_VERSION / kind / f"{remote_stem}.webp",
        webp_bytes,
    )


def _iter_inputs(kinds: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for kind in kinds:
        d = INPUTS_ROOT / kind
        if not d.exists():
            continue
        for p in sorted(d.iterdir()):
            if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg"):
                files.append(p)
    return files


def publish_all(styler_factory: StylerFactory) -> int:
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    files = _iter_inputs((DEDICATED, STOCK))
    if not files:
        print("no input files found under app/imaging/inputs/")
        return 0
    for path in files:
        publish_image(path, styler_factory, bucket)
    print(f"done, published {len(files)} files")
    return len(files)
