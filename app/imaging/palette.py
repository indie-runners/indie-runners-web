"""Palette resolution for the duotone styler.

Terrain is parsed from filename prefix. Per-terrain palettes come from a
JSON config; global CLI hex flags fill missing components; DuotoneStyler
class defaults are the final fallback.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from app.imaging.stylers import DuotoneStyler

TERRAINS = ("trail", "road", "mixed")
PALETTE_COMPONENTS = ("shadow", "mid", "highlight")

RGB = tuple[int, int, int]


def parse_hex(value: str) -> RGB:
    s = value.strip().lstrip("#")
    if len(s) != 6:
        raise ValueError(f"invalid hex color: {value}")
    try:
        return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    except ValueError:
        raise ValueError(f"invalid hex color: {value}")


def terrain_from_filename(path: Path) -> str:
    prefix = path.stem.split("_", 1)[0].lower()
    if prefix not in TERRAINS:
        raise ValueError(
            f"filename must start with a terrain prefix (one of {TERRAINS}): {path.name}"
        )
    return prefix


def load_duotone_config(path: Path) -> dict[str, dict[str, RGB]]:
    with path.open() as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"duotone config root must be a JSON object: {path}")
    out: dict[str, dict[str, RGB]] = {}
    for terrain, palette in data.items():
        if terrain not in TERRAINS:
            raise ValueError(
                f"duotone config has invalid terrain '{terrain}' (allowed: {TERRAINS})"
            )
        if not isinstance(palette, dict):
            raise ValueError(f"duotone config entry for '{terrain}' must be an object")
        parsed: dict[str, RGB] = {}
        for component, hex_value in palette.items():
            if component not in PALETTE_COMPONENTS:
                raise ValueError(
                    f"duotone config for '{terrain}' has invalid component "
                    f"'{component}' (allowed: {PALETTE_COMPONENTS})"
                )
            parsed[component] = parse_hex(hex_value)
        out[terrain] = parsed
    return out


def resolve_duotone(
    terrain: str,
    config: dict[str, dict[str, RGB]],
    global_shadow: Optional[RGB],
    global_mid: Optional[RGB],
    global_highlight: Optional[RGB],
) -> DuotoneStyler:
    terrain_palette = config.get(terrain, {})
    shadow = terrain_palette.get("shadow") or global_shadow
    mid = terrain_palette.get("mid") or global_mid
    highlight = terrain_palette.get("highlight") or global_highlight
    return DuotoneStyler(shadow=shadow, mid=mid, highlight=highlight)
