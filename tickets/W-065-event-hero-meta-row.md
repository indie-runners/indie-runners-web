# W-065 — Every event hero's meta row starts with "·", and names the country in lower case

`priority: 3` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/DEV_NOTES.md 2026-10-27 (while on W-013), confirmed live at triage 2026-10-28`

## What is wrong

Two defects in one row, `app/templates/event.html:41-60`.

1. **The separator belongs to the item after it, so a missing first item
   leaves a leading `·`.** The location `<span>` has no separator; country
   and date each open with one. `event_location` is NULL on every event in
   the view (0 of 396, read-only query 2026-10-28), so every event page
   starts its meta row with `·`.
2. **The country prints raw.** The view's `event_country_code` is a
   lowercased name. The index dropdown (`index.html:49`) and `/stats`
   (`stats.html:45`) pipe it through `| title`; the hero does not, and
   `.event-meta-item` has no `text-transform`.

## Evidence

`curl -s https://indierunners.co/events/athens_authentic_marathon/2026`,
serving `indie-runners-web-00064-l84`, 2026-10-28:

```html
<div class="event-meta">
  <span class="event-meta-sep">·</span>
  <span class="event-meta-item">greece</span>
  <span class="event-meta-sep">·</span>
  <span class="event-meta-item">
      7 November
  </span>
</div>
```

Multi-word values in the view today: `bosnia and herzegovina`, `north
macedonia`, `south africa`, `united kingdom` (25 events), `united states`.
NULL on 3 events (`hochkoenigman`).

## Acceptance

1. No meta row begins or ends with a separator, whichever items are
   present, including country NULL (`hochkoenigman`) and TBC.
2. The country reads as the index and `/stats` read it (`Greece`,
   `United Kingdom`). Use the same filter they use.
3. Rendered signed out and signed in: Athens, one UK event, `hochkoenigman`
   and one TBC event. Quote the meta row HTML in the changelog.

## Out of scope

- **The location value.** W-070 (next after this) gives the hero a town
  through one shared cascade. Here the row just has to render right with
  the location item absent, which it is on every event today.
- The Kosovo/Comoros names (scraper T-147, routed check 18).
- The date text itself (W-047, done).

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-071** — 2026-10-28. The changelog
names the wrong belief (the first item is always there), its cost and the
new rule. The diff is the template only, and the date arm keeps its three
branches. Verified by the developer from this worktree on :8000
(`/proc/<pid>/cwd`), anon and with a minted cookie for user 15: Athens,
a UK range, `hochkoenigman` (NULL country) and a TBC event, rows quoted.
No ARCHITECTURE or FILE_TREE change is needed. Docs: 35 lines. W-071 is the
"Bosnia And Herzegovina" that `| title` gives, which my spec asked for.
Ticket is `deploy: batched`.

**Not verified:** a location item through the live route. None exists
until W-070, so it was shown only as a fragment rendered directly. Also
not run: a TBC event with no `tbc_display`, which falls through to the
date branches. That logic is unchanged from master. W-070's review covers
the first, because W-070 fills the location.
