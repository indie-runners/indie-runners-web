# TODO: #35 — the sign-in request carries no OAuth state

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-20_

## Steps

- [ ] `/auth/google`: fresh `secrets.token_urlsafe` in `session["oauth_state"]` on every hit (bare Try again included), sent as `state`
- [ ] Callback: pop `oauth_state` first (used once on every path); no-`code` branch unchanged; then compare before any code exchange
- [ ] Mismatch shares the `CodeExchangeRefused` handling: signed in → 303 to the queued redirect or `/` (W-094); signed out → `signin_failed.html` 400
- [ ] Compare bytes, guard `None`: `compare_digest` raises on `None` and non-ASCII `str`
- [ ] ARCHITECTURE: flow (§ sign-in), session paragraph, the event-page "no `state` round-trip" line
- [ ] Changelog 1.9.88

## Measure

- Authorize `Location` carries `state`, equal to the cookie's
- Forged / missing `state` → 400 sign-in-failed page; cancel → 303 `/`; signed-in mismatch → 303
- Matching `state` + bogus code → Google refuses → sign-in-failed (state check passed)

## Unsure

- A full Google round trip (event `next`, `/settings`, invite stash) needs a browser and an account: ask Paulo, or say plainly it was not exercised
