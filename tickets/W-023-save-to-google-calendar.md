# W-023 — Offer "Save to Google Calendar" after marking interested / going

`priority: 4` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-10-21 (Paulo), "Save to calendar"`

## The ask

When a user marks themselves interested or going (`POST
/events/{event_id}/{occurrence_id}/attendance`, `app/main.py:303`), offer
a "Save to Google Calendar" link. **Google only.** This is a feature that
arrived through IDEAS, which is the door PLAN admits features through.

Paulo's hunch, unverified: the template link
`calendar.google.com/calendar/render?action=TEMPLATE&...` needs no extra
OAuth scope. **Verify that first.** If it needs a scope, stop. Touching
sign-in is band 1 risk for a band 4 feature.

## Traps

- **All-day dates.** `dates=YYYYMMDD/YYYYMMDD` has an **exclusive** end,
  so a one-day race on Oct 25 is `20261025/20261026`. Multi-day events
  span to the last race + 1. Getting this wrong renders a plausible link
  one day short.
- **TBC events have no date** (`format_tbc_expected`). Show no link
  there, rather than a month guess.
- Event-level, not per race. Title and dates come from the event, and
  location from the existing location field. Escape everything that goes
  into the URL.
- The link appears where the user marked: the event page and the tile, if
  both offer marking. Anon users never see it.

## Acceptance

1. After marking interested or going on a dated event, the link opens
   Google Calendar prefilled with the right title and the right dates
   (check a single-day and a multi-day event, named).
2. TBC event: no link.
3. Signed-in tier only. Anon unchanged (check it).
4. No new OAuth scope, and the sign-in flow untouched.
5. Changelog entry.

## Out of scope

- `.ics` download, Apple and Outlook. "Google only for now" is the ask.
- Calendar sync or updates when a date changes.
- Start times. Races carry `start_time`, but an all-day entry is the
  smallest honest shape. Say in the close-out if that looks wrong.

## Amended at handover (Paulo, 2026-10-27)

Only **going** offers it, as a one-time popup when the POST returns
`going`. Interested triggers nothing, and no standing link is left on the
page. This replaces "a link where the user marked" in acceptance 1 and 3.
Acceptance 1 now reads: after marking going on a dated event, the popup
offers a link with the right title and dates.

## Verdict

**VERDICT: BLOCKED — R1** — 2026-10-27.

**R1, an overstated claim.** The changelog says "Both surfaces span first
to last **race** date." On the tile that's only true unfiltered. `list_races`
filters races before grouping, so `date_from`/`date_to` and `search` shrink
the span, and the popup then offers a link that's a day short (Athens,
`date_to=2026-11-07`, gives `20261107/20261108`). The code defect predates
this branch and is now W-061. **What unblocks it:** the changelog says the
tile spans the races the listing returned, narrowed by filters (W-061) and
by the past-race cut (W-012). That also answers the TODO's open question.
No code change asked.

Passed: the no-scope claim checks out (plain link, sign-in untouched).
Exclusive end and `urlencode` are correct. TBC and missing date give no
URL. The dialog and URL are signed-in only. The worktree's own server was
checked by `/proc/<pid>/cwd`. Docs are 59 of 100 lines, 1.9.42.

Dropped, not filed: a click on the dialog's 24px padding counts as a
backdrop click and closes it. That only dismisses a "Not now" offer.

**Not verified:** Google's prefilled form, and the popup on a real screen.
The changelog says neither ran. Commit 8ea6494 ("centre the calendar
popup") suggests someone looked, but nothing records that it was seen.
Real `showModal` was never run either, since jsdom stood it in with `open`.
One click on a real signed-in browser settles both.

## Verdict (re-review)

**VERDICT: APPROVED WITH FOLLOW-UPS — W-061** — 2026-10-27. R1
resolved: the changelog now says the tile spans the races the listing
returned, narrowed by filters (W-061) and the past-race cut (W-012).
Paulo saw the popup on a real screen, signed in, through real
`showModal`, centred after 8ea6494. Docs are 63 of 100 lines. The ticket
is `deploy: batched`. Routed check 28.

**Not verified:** Google's prefilled form, meaning the title, dates and
location as Google parses them. One click on "Save to Google Calendar"
from a dated multi-day event settles it. The Athens one-day-short link
under `date_to` comes from reading the code and was never rendered. It
belongs to W-061.
