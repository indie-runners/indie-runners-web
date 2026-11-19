# TODO: #53 — a new user's source is lost at Google sign-in

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-19_

## Steps

- [x] Migration 016: six nullable signup_* columns on web.users (written; Paulo applies)
- [x] Source read at Sign in from the `next` URL, not on arrival: no cookie before Sign in (Paulo, 2026-11-19)
- [x] Every anon Sign in link keeps the full URL (`signin_url_for`), or a landing page's utm is lost
- [x] Written only when a user row is created; cancel clears it
- [x] Growth script line 6; privacy.html
- [ ] Paulo applies 016, then verify: fresh user via utm link, fresh user via invite, returning user
- [ ] ARCHITECTURE, CHANGELOG, FILE_TREE

## Measure

- The three users' signup_* values after sign-in (to `evidence #53`)

## Unsure

- Fresh sign-ins need Google accounts that never used the site, or test rows deleted between tries

## What the work showed

- Spec said keep the first utm in the session on arrival; that is a measurement cookie before sign-in. Paulo: only those who sign in straight from the link count, no cookie before Sign in
- The code must not deploy before 016: every query that loads a User names the new columns
