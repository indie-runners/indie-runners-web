# W-036 — ARCHITECTURE and a code comment say there is no `?next=` parameter

`priority: 5` · `effort: S` · `area: docs` · `deploy: batched`
`source: W-035 review, 2026-10-23`

## What is wrong

`docs/ARCHITECTURE.md:238`:

> Only server-set redirects are honoured; there is no `?next=` query
> parameter, so no open-redirect surface.

The callback comment in `app/main.py:851-853` says the same: "Only routes
we control ever set this key, so there is no open-redirect surface."

Both are false. `GET /auth/google?next=…` stashes a caller-supplied
value after `_validate_next`. `ARCHITECTURE.md:169` says so, and the
event page's sign-in buttons and W-035's `/settings` redirect use it. The
document contradicts itself on a security property. A reader who trusts
:238 would skip `_validate_next` when touching the redirect.

## Acceptance

1. :238 says that `next` exists and is validated, and points to :169
   rather than repeating the rules.
2. The callback comment says the key holds either a server-set value or
   a `_validate_next`-checked one.
3. No behaviour change. The diff touches only that comment and docs.

## Out of scope

- Changing `_validate_next` or adding an OAuth `state` round trip.
