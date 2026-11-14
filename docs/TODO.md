# TODO: #32 — A signed-out visitor on a crew link gets a bare 401

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-14_

- [ ] `/crews/{slug}` anon: 200 `crews_hidden.html` + Sign in link, `next` keeps the query string
- [ ] `/crews`, `/crews/new`, `/profile` anon: 303 to `/auth/google?next=…` (the `/settings` mechanism)
- [ ] Measure: anon GET/HEAD on all four, real and made-up slug (same body); member and non-member signed in
- [ ] Unsure: `next` with a query string must be URL-encoded or `?joined=1` is lost to `/auth/google`'s own query
- [ ] ARCHITECTURE § Crews line; changelog
