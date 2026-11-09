# W-075 — A `?v=` that names another revision's file is cached for a year

`priority: 3` · `effort: S` · `area: templates` · `deploy: batched`
`source: W-074 review, 2026-10-30`

## What is wrong

`StaticCacheMiddleware` (1.9.48) answers any `/static/` request carrying
a `v` query parameter with `Cache-Control: public, max-age=31536000,
immutable`. It never compares `v` with the file it serves, and
`StaticFiles` ignores the query string. So the docstring's premise, "a
versioned URL never changes content", holds only while every instance
serves the same image.

It stops holding whenever two revisions answer one browser: the seconds
around a deploy's traffic switch, a rollback (`deploy.sh` prints an
`update-traffic --to-revisions=$PREVIOUS=100` line), or a pin (W-068).
A page from revision A names `main.css?v=<A's hash>`. If that fetch lands
on revision B, the browser stores B's bytes under A's URL as immutable.
When A serves again (the rollback), that browser pairs A's HTML with B's
CSS or JS for up to a year, and only clearing the cache fixes it. That is
W-064's defect again, with a longer lifetime.

## Evidence

`app/main.py` on `fix/gcal-popup-silent`:

```
        if request.url.path.startswith("/static/"):
            versioned = "v" in request.query_params
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable" if versioned else "no-cache"
```

Latent: no rollback or split has happened since 1.9.48. Not observed.

## Acceptance

1. `immutable` only when `v` equals the hash `static_url` gives the
   requested path in this process. Any other `v`, and no `v`, gets
   `no-cache`.
2. Locally: `?v=<the real hash>` → immutable; `?v=deadbeef` → `no-cache`,
   `200`, same body; a 404 → `no-cache`.
3. The docstring states the rule it now enforces.

## Out of scope

- Hash by mtime, or dev-mode no-cache (the DEV_NOTES `shortcut:`).
- Fingerprinted filenames instead of a query string.
- W-068's traffic-pin guard.
