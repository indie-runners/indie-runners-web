# W-113 — `_REDIRECTED_HOSTS` still lists the unmapped `beta` host

`priority: 5` · `effort: S` · `area: routing` · `deploy: batched`
`source: docs/DEV_NOTES.md 2026-11-09 (while on W-018)`

## What is wrong

W-018 removed the `beta.indierunners.co` domain mapping on 2026-11-09, but
`app/main.py` still redirects that host. The entry is dead code, and
ARCHITECTURE has to explain why it is still there.

## Evidence

`app/main.py:69`:

```
_REDIRECTED_HOSTS = {"beta.indierunners.co", "www.indierunners.co"}
```

`docs/ARCHITECTURE.md:562`: *"301-redirects `www` (and `beta`, still in
`_REDIRECTED_HOSTS`, though it no longer reaches the app) to the apex host"*.

## Acceptance

1. `_REDIRECTED_HOSTS` holds only `www.indierunners.co`.
2. ARCHITECTURE:562 no longer mentions `beta` in `_REDIRECTED_HOSTS`. The
   sentence saying it was unmapped on 2026-11-09 stays.
3. Locally, a request with `Host: www.indierunners.co` still gets a `301`
   to the apex, and a request with `Host: indierunners.co` gets a `200`.

## Out of scope

- `_CANONICAL_HOST`, the status code, or the middleware's order. W-017
  settled those.
- DNS, mappings and OAuth URIs. W-018 removed them, and they belong to
  infra.
