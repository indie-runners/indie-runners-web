from app.config import settings

BASE_URL = "https://storage.googleapis.com/indie-runners-web-tiles/tiles"


def resolve_tile_image(event_slug: str, event_image, dedicated_slugs: set[str]) -> str:
    version = settings.tile_version
    if event_slug in dedicated_slugs:
        return f"{BASE_URL}/{version}/dedicated/{event_slug}.webp"
    return f"{BASE_URL}/{version}/stock/{event_image.stock_filename}.webp"
