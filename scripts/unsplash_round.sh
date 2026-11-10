#!/bin/bash
# One Unsplash round: fetch, manifest, publish, restart, backfill.
#
#   bash scripts/unsplash_round.sh <file>
#
# <file> has one event per line: `<slug> [query]`. The query is the rest of
# the line and may contain spaces. Blank lines and lines starting with # are
# ignored. Choosing the events is photo_candidates.py's job, before this.
#
# DATABASE: unsplash_fetch.py reads the index and the backfill writes
# web.event_images, both through DATABASE_URL (.env), so the Cloud SQL proxy
# must be up (scripts/db_proxy.sh) and the whole run is the one DB-touching
# session allowed across both repos.
#
# Why the backfill is not optional: the restart reloads the dedicated slugs
# from GCS, so the new tiles appear, but the credits come from the manifest
# baked into the serving image, which predates this round. Startup skips any
# slug that manifest lacks, so only the backfill writes the new credits.
#
# The restart is the path rounds have used so far: `gcloud run deploy` of the
# serving revision's own image digest. Same code, same config, new revision.
# It touches production, so it asks first.
set -uo pipefail

PROJECT="indie-runners-dev-470411"
REGION="europe-west1"
SERVICE="indie-runners-web"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LIST="$(realpath "${1:?usage: bash scripts/unsplash_round.sh <file of slug [query] lines>}")"
cd "$ROOT"

BACKFILLED=0
trap '[[ $BACKFILLED == 1 ]] || {
  echo >&2
  echo "BACKFILL NOT RUN: the new photos (if published) still carry the old credits." >&2
  echo "Once the restart has happened: python scripts/backfill_event_image_attribution.py" >&2
}' EXIT

step() {  # step <name> <command...>: run it, or stop the round naming the step
  local name="$1"; shift
  echo; echo "== $name"
  "$@"; local rc=$?
  ((rc == 0)) || { echo >&2; echo "STOPPED at step: $name (exit $rc)" >&2; exit 1; }
}

# Fetch. fd 3 carries the list so the photo pick keeps the terminal as stdin.
while read -r slug query <&3; do
  [[ -z "$slug" || "$slug" == \#* ]] && continue
  if [[ -n "$query" ]]; then
    step "fetch $slug" python scripts/unsplash_fetch.py "$slug" --no-publish --query "$query"
  else
    step "fetch $slug" python scripts/unsplash_fetch.py "$slug" --no-publish
  fi
done 3< "$LIST"

step "manifest" python scripts/generate_dedicated_manifest.py
step "publish" python -m app.imaging --style passthrough --tile-version v02

echo; echo "== restart"
step "restart: read serving revision" bash scripts/deploy.sh --check
REV="$(gcloud run services describe "$SERVICE" --region="$REGION" --project="$PROJECT" \
  --format='value(status.traffic[0].revisionName)')" || { echo "STOPPED at step: restart" >&2; exit 1; }
DIGEST="$(gcloud run revisions describe "$REV" --region="$REGION" --project="$PROJECT" \
  --format='value(status.imageDigest)')" || { echo "STOPPED at step: restart" >&2; exit 1; }
echo "image             : $DIGEST"
read -r -p "Create a new production revision from this image? [y/N] " ok
[[ "$ok" == y ]] || { echo "STOPPED at step: restart (declined)" >&2; exit 1; }
step "restart" gcloud run deploy "$SERVICE" --image "$DIGEST" \
  --region "$REGION" --project "$PROJECT" --platform managed
step "restart: read new revision" bash scripts/deploy.sh --check

step "backfill (sets the credits)" python scripts/backfill_event_image_attribution.py
BACKFILLED=1

echo
echo "Round done. Commit docs/dedicated_credits.md and app/imaging/dedicated_manifest.json"
echo "so the next deploy bakes this round's manifest."
