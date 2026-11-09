#!/bin/bash
# Build, push and deploy the web service to Cloud Run.
#
# This points a public site at whatever this script builds, so the guards
# below are not conveniences.
#
# What is guarded and why:
#
#   Dirty tree      An image built from uncommitted code exists in no
#                   commit, so the revision it produces cannot be rebuilt
#                   from git. That is only a problem when something goes
#                   wrong — which is exactly when a rollback target is
#                   needed. Same reason the scraper's deploy.sh refuses.
#
#   Serving revision  Printed before traffic moves. Cloud Run keeps old
#                   revisions, so a rollback target exists; it is just
#                   not knowable after the fact without going and looking
#                   it up. Recording it costs one read-only call.
#
#   Rollback line   Printed after, naming the revision that was serving.
#                   An operator at 2am should not have to compose it.
#
# What is deliberately NOT guarded:
#
#   Tests           There is no test suite in this repo (backlog W-003).
#                   A gate on a suite that does not exist would be a
#                   comment, not a guard.
#
#   Version         The scraper's deploy.sh reads a version from
#                   docs/CHANGELOG.md because it tags images with it and
#                   rolls back by tag. This service deploys an untagged
#                   image and Cloud Run names the revision itself, so
#                   there is no version stream here to keep in step —
#                   the revision name is the identifier that matters.
#
#   ./scripts/deploy.sh           # build and deploy
#   ./scripts/deploy.sh --check   # print the serving revision, change nothing
#
set -euo pipefail

PROJECT="indie-runners-dev-470411"
REGION="europe-west1"
SERVICE="indie-runners-web"
IMAGE="gcr.io/$PROJECT/$SERVICE"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

serving_revision() {
  gcloud run services describe "$SERVICE" \
    --region="$REGION" --project="$PROJECT" \
    --format="value(status.traffic[0].revisionName)"
}

# Not silenced, and the failure is named. Under `set -e` a failing gcloud
# here would otherwise kill the script with no output at all — including
# in --check — and expired auth is the likeliest reason it fails.
if ! PREVIOUS="$(serving_revision)"; then
  echo >&2
  echo "Could not read the serving revision. Check gcloud auth and that" >&2
  echo "$SERVICE exists in $REGION. Not deploying: without a rollback" >&2
  echo "target there is nothing to go back to." >&2
  exit 1
fi
echo "currently serving : ${PREVIOUS:-<none>}"

if [[ "${1:-}" == "--check" ]]; then
  exit 0
fi

# An image built from uncommitted code cannot be rebuilt from git, so the
# revision it produces has no reproducible source.
if [[ -n "$(git status --porcelain)" ]]; then
  echo >&2
  echo "Working tree is dirty. Commit or stash first — otherwise the image" >&2
  echo "carries code that exists in no commit and cannot be rebuilt." >&2
  git status --short >&2
  exit 1
fi

echo "deploying commit  : $(git rev-parse --short HEAD)"
echo
echo "Building and pushing image..."
gcloud builds submit --tag "$IMAGE" --project "$PROJECT"

echo "Deploying to Cloud Run..."
# Image and where only. The service's shape (scaling, memory, secrets, env, Cloud SQL,
# public access) is declared in indie-runners-infra/web/; without shape flags,
# gcloud run deploy keeps the live config.
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --project "$PROJECT" \
  --platform managed

CURRENT="$(serving_revision || true)"

echo
echo "Deployed. Service URL:"
gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT" --format "value(status.url)"
echo "now serving       : ${CURRENT:-<unknown>}"

if [[ -n "$PREVIOUS" && "$PREVIOUS" != "$CURRENT" ]]; then
  cat <<ROLLBACK

Roll back to $PREVIOUS:
    gcloud run services update-traffic $SERVICE --region=$REGION \\
        --project=$PROJECT --to-revisions=$PREVIOUS=100

That pins traffic to one revision, so the next deploy of this script will
create a revision that receives none. Return to serving the newest with:
    gcloud run services update-traffic $SERVICE --region=$REGION \\
        --project=$PROJECT --to-latest
ROLLBACK
fi
