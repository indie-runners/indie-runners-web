# TODO: W-112 — Every deploy installs whatever Python packages are newest that day

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-09_

## Steps
- [x] `pip freeze` of the serving image (00094-862, digest in spec) → `requirements.lock`
- [x] Dockerfile installs the lock; `requirements.txt` comment points at it
- [x] Local image freeze vs live freeze: empty diff (evidence W-112)
- [x] Local image serves both tiers
- [x] CHANGELOG, FILE_TREE

## Unsure / disproved
- The base tag `python:3.11-slim` still floats (out of scope). Both images
  run 3.11.18 today. A 3.12 tag move would break the cp311 wheels loudly
  at build time, not silently.
- The regenerate command in the lock's header resolves fresh, so an
  upgrade moves every transitive too. That's intended: it's a deliberate
  diff someone reviews.
