# W-074 — The Save-to-Google-Calendar popup no longer opens on production

`priority: 2` · `effort: S` · `area: templates` · `deploy: immediate`
`source: Paulo, 2026-10-30 (terminal, PM session)`

## What is wrong

Signed in on indierunners.co, clicking Going on a dated event — index
tile or event page, desktop or phone, Chrome and Firefox — marks the row
(the POST answers 200, the button flips) and opens nothing. W-023's
popup (1.9.42) opened on production under `00064-l84`; Paulo saw it. Under
`00065-mzr` it does not. Every click lands on one of the four silent exits
in `attendance.js`:

```
          if (action === 'going' && data.user_status === 'going') offerCalendar(tile);
  ...
    if (!dialog || !url || !dialog.showModal) return;
```

or `updateTile(tile, data)` throws before `offerCalendar` runs (a
rejected promise, nothing on screen).

## Evidence — what is ruled out (PM, 2026-10-30)

- Request log, last three days: every `POST /events/*/attendance` is
  `200` (Firefox desktop 11:05Z and 10:59Z, Android Chrome 29 Oct 20:00Z).
  Both occurrences are dated: `kullamannen` 96715 (30–31 Oct 2026),
  `gorlicki_bieg_gorski` 132581 (7 Nov 2026). Neither is TBC, so
  `data-gcal-url` is rendered and `user_status` is int-keyed
  (`_attendance_response`, `get_attendance_for_user`).
- The Cloud Build source tarballs of `00064` (build 2026-10-27T23:09) and
  `00065` (2026-10-28T15:17) differ in **one** application file,
  `app/templates/event.html` (W-065 hero row, W-066 wording). `base.html`,
  `attendance.js`, `main.css`, `partials/race_tile.html`, `main.py` are
  byte-identical. The index does not render `event.html`, and it fails too.
- `gcloud run revisions describe` on both: same env, image args, service
  account, resources. Only nonce, generation and health messages differ.
- Production serves `attendance.js` equal to `e45a311`'s (fetched and
  diffed), with `showModal`; browsers revalidate it (`304`s on 30 Oct), so
  W-064's missing cache policy is not holding an old copy.
- Not seen: a signed-in production page, the POST's JSON in a browser, the
  console. Chrome is not connected to the PM session.

## Acceptance

0. **Name the exit first, quoted in the changelog.** On indierunners.co,
   signed in, on an event page, before clicking:
   `[document.querySelectorAll('.gcal-dialog').length, document.querySelector('.event-attendance')?.dataset.gcalUrl, typeof document.createElement('dialog').showModal]`
   then Remove → Going, the POST's response body, and any console error.
   If it does not reproduce locally against the `00065` source with a
   minted cookie, say so: the difference is then environmental, not code.
1. Signed in on indierunners.co, clicking Going on a dated event opens
   the dialog, from an index tile and from the event page, in a real
   browser, desktop and phone. Interested still opens nothing; a TBC
   tile still opens nothing.
2. Changelog names the wrong belief and what the evidence was.

## Out of scope

- A cache policy or versioned asset URLs — W-064.
- The tile span following filters — W-061.
- Any change to what the popup offers (Google only, going only, once).

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-075** — 2026-10-30. The ticket's
premise was wrong, and the PM's "stale JS ruled out" line with it: `304`s
from other clients said nothing about Paulo's Firefox, which served a
9,336-byte pre-W-023 `attendance.js` from cache (`transferSize 0`) under a
response with no `cache-control`. Chrome desktop on `00065` opened the
popup from both surfaces. W-064 folded in on Paulo's word. Every
`/static/` reference in templates goes through `static_url` (none left by
hand in templates, JS or CSS). Middleware order and headers were checked
on :8000 from this worktree, anon and signed in (minted cookies, users 1
and 12). Docs 71 lines. `deploy: immediate`. Routed check 35.

W-075: `immutable` is set on any `?v=`, matching or not, so a
cross-revision fetch (deploy switch, rollback, pin) can cache the wrong
bytes for a year. Latent; it needs a rollback or split to fire.

**Not verified:** the popup on production after deploy in Firefox and on
Android Chrome without a hard reload. Paulo settles that (TODO's last
box). Android was never diagnosed: its log fits the same cause (it
fetched pages on 27 Oct 13:17Z, ten hours before `00064` went live, then
posted on 29 Oct), but nobody saw its cache. Rollback behaviour of the
versioned URLs (W-075). The local `--reload` shortcut (DEV_NOTES).
