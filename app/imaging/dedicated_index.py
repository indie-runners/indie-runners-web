"""Set of event_slugs that have a dedicated tile photo in GCS.

Source of truth is the bucket's `originals/dedicated/` prefix — one blob
per dedicated event. Loaded once at app startup and held in memory. To
pick up a new dedicated photo after publish, restart the app.

The `indie-runners-web-tiles` bucket allows anonymous listing (uniform
access, allUsers = Storage Object Viewer), so no ADC required.
"""

from __future__ import annotations

from pathlib import PurePosixPath

from google.cloud import storage

BUCKET_NAME = "indie-runners-web-tiles"
PREFIX = "originals/dedicated/"


def load_dedicated_slugs() -> set[str]:
    client = storage.Client.create_anonymous_client()
    bucket = client.bucket(BUCKET_NAME)
    slugs: set[str] = set()
    for blob in client.list_blobs(bucket, prefix=PREFIX):
        name = blob.name
        if not name.lower().endswith((".jpg", ".jpeg")):
            continue
        stem = PurePosixPath(name).stem
        if stem:
            slugs.add(stem)
    return slugs
