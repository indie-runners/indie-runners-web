# W-085 — A signed-out visitor on a crew link gets a bare 401

`priority: 3` · `effort: S` · `area: routing` · `deploy: batched`
`source: W-077 review 2026-10-31 (DEV_NOTES 2026-10-31, while on W-077)`

## What is wrong

Three HTML pages depend on `get_required_user`, which raises
`HTTPException(401)` for anon: `GET /crews/{slug}`, `GET /crews/new` and
`GET /profile`. A signed-out visitor gets `{"detail":"not authenticated"}`
instead of sign-in and back. W-077 made the crew page a hub, the URL a
member is most likely to paste to someone, so the crew link is the one
that will be hit.

`/settings` already solved this (`main.py:646`): it takes
`get_current_user` and redirects. ARCHITECTURE § Crews describes that
behaviour for the crew page, which doesn't have it.

## Evidence

DEV_NOTES 2026-10-31: *"On master (checked with the branch stashed)
`curl localhost:8000/crews/<crew>` is a bare 401 from
`get_required_user`; only `/settings` has the redirect (main.py:646)."*

`app/main.py:644-649`:

```
    # Public pages (privacy §8, terms §9) link here, so a signed-out
    # reader goes through sign-in and back rather than to a bare 401.
    if current_user is None:
        return RedirectResponse("/auth/google?next=/settings", status_code=303)
```

`docs/ARCHITECTURE.md:204`: *"an unauthenticated visitor bounces to
Google rather than seeing a placeholder"*.

## Acceptance

1. Anon `GET` on `/crews/{slug}`, `/crews/new` and `/profile` → 303 to
   sign-in; after signing in the visitor lands on the URL they asked for,
   query string kept (`/crews/{slug}?view=going`). Use the mechanism
   `/settings` or `/crews/join/{token}` already uses, not a third.
2. A signed-in non-member on `/crews/{slug}` still gets `crews_hidden.html`
   (the redirect must not leak whether the slug exists: anon gets the same
   303 for a real and a made-up slug).
3. `HEAD` answers like `GET` on all three (routed check 1).
4. ARCHITECTURE § Crews matches what the route does.
5. Verified anon and signed in, both a real and a made-up slug.

## Out of scope

- POST routes and `/me`: a 401 is the right answer for a form post or an
  API call made without a session.
- A global 401 handler: three routes, and `/settings` shows the per-route
  pattern is enough.

**Amended at the W-078 review, 2026-10-31:** W-078 adds a fourth,
`GET /crews` (the nav's Crews item, a 303 to the hub or the profile). Anon
gets the same bare 401. Only the signed-in menu links to it, so it is hit
only as a pasted URL, but it goes in acceptance 1 with the other three.
