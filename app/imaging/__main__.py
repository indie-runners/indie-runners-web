import argparse
import sys
from pathlib import Path

from app.imaging import publish as publish_mod
from app.imaging.palette import (
    load_duotone_config,
    parse_hex,
    resolve_duotone,
    terrain_from_filename,
)
from app.imaging.publish import publish_all
from app.imaging.stylers import ColorGradeStyler, ImageStyler, PassthroughStyler

STYLERS = {
    "grade": ColorGradeStyler,
    "passthrough": PassthroughStyler,
}


def _hex_or_none(v):
    return parse_hex(v) if v else None


def _build_factory(args):
    if args.style != "duotone":
        cls = STYLERS[args.style]
        instance = cls()
        return lambda _path: instance

    config = load_duotone_config(Path(args.duotone_config)) if args.duotone_config else {}
    globals_shadow = _hex_or_none(args.shadow)
    globals_mid = _hex_or_none(args.mid)
    globals_highlight = _hex_or_none(args.highlight)

    cache: dict[tuple, ImageStyler] = {}

    def factory(path: Path) -> ImageStyler:
        terrain = terrain_from_filename(path)
        styler = resolve_duotone(
            terrain,
            config,
            globals_shadow,
            globals_mid,
            globals_highlight,
        )
        key = (styler.shadow, styler.mid, styler.highlight, styler.contrast)
        cached = cache.get(key)
        if cached is None:
            cache[key] = styler
            cached = styler
        return cached

    return factory


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.imaging")
    parser.add_argument(
        "--style",
        choices=["duotone", "grade", "passthrough"],
        required=True,
    )
    parser.add_argument(
        "--tile-version",
        default=publish_mod.TILE_VERSION,
        help="target tile version prefix in the bucket (default: %(default)s)",
    )
    parser.add_argument(
        "--shadow",
        help="duotone shadow color as #RRGGBB or RRGGBB (applies when --style duotone)",
    )
    parser.add_argument(
        "--mid",
        help="duotone mid color as #RRGGBB or RRGGBB (applies when --style duotone)",
    )
    parser.add_argument(
        "--highlight",
        help="duotone highlight color as #RRGGBB or RRGGBB (applies when --style duotone)",
    )
    parser.add_argument(
        "--duotone-config",
        help="path to JSON file mapping terrain -> {shadow, mid, highlight} hex triples",
    )
    args = parser.parse_args()

    if args.style != "duotone" and (
        args.shadow or args.mid or args.highlight or args.duotone_config
    ):
        print(
            "warning: --shadow/--mid/--highlight/--duotone-config are ignored when --style is not duotone",
            file=sys.stderr,
        )

    publish_mod.TILE_VERSION = args.tile_version

    try:
        factory = _build_factory(args)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(f"publishing to tiles/{args.tile_version}/ with styler {args.style}")
    try:
        publish_all(factory)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
