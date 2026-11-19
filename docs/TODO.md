# TODO: #52 — a crew invite link shows nothing about the crew before Google sign-in

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-19_

## Steps

- [x] Signed out, valid token: `crews_invite_preview.html` (name, member count, planned races, Sign in)
- [x] Sign in returns through `?next=`; header Sign in carries it on this page
- [x] Invalid or rotated token signed out: `crews_invite_invalid.html`
- [x] Verify anon (curl, headless Chrome) and signed in (minted cookie); robots.txt
- [x] ARCHITECTURE § Crews, FILE_TREE, changelog

## Measure

- Preview counts equal the hub's member and agenda rows for the same crew

## Unsure

- The Google round trip back to the confirm page was not run; `?next=` is the path `/crews/<slug>` already uses

## What the work showed

- The hub's agenda rows don't depend on the viewer, only the names on them do, so the count needs no visibility rule
- The site header's Sign in dropped the invite; it now carries `next` on this page only
