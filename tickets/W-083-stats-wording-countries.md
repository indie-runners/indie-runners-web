# W-083 — /stats: "checked" is unclear, and the country list reads as a ranking

`priority: 3` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-10-30 (Paulo, user feedback)`

**NOT THE NEXT TICKET:** the crews arc goes first (`docs/PLAN.md`).

## What is wrong

Users told Paulo the word "checked" on `/stats` is unclear. The country list
under the map is an `<ol>` ordered by count, so it reads as a ranking.

## Evidence

Paulo, IDEAS 2026-10-30: *"I got feedback from users that the word checked is not clear. Maybe elaborate more on it."* His draft copy:

> This is the total number of events we look at and follow at indie runners. Whether or not it has a date coming up. -- notice lower case
>
> We fetch information from all the event we follow on a constant basis, so that we can keep you up to date with what is going in.

and: *"Please remove the rank and simply list the countries alphabetically. So instead of having numbers, just two columns with the list of countries alphabetically, with their respective numbers."*

`stats.html` today:

```
  <h2>{{ tracked }} events tracked</h2>
  <p>Every event Indie Runners follows, whether or not it has a date coming up.</p>

  <h2>{{ checked_30d }} events checked in the last 30 days</h2>
  <p>Upcoming events whose details we went back and looked at.</p>
```
```
  <ol class="stats-countries">
    {% for c in countries %}
      <li><a href="/?country={{ c.name | urlencode }}">{{ c.name | title }}</a> — {{ c.n }}</li>
```

## Acceptance

1. Both descriptions carry Paulo's meaning with his slips fixed ("all the events", "what is going on"). "Tracked": one sentence, "whether or not…" in lower case, which is how the PM reads "notice lower case". "Checked": says we re-fetch each followed event's details regularly to keep the site current. The headings stay.
2. Countries: an unnumbered list, alphabetical by the name as displayed, two columns (one on narrow screens), each with its count and link as now.
3. Verified anon at desktop and 375px. The map and its links are unchanged.

## Out of scope

- "Bosnia And Herzegovina" (W-071).
- The numbers themselves, and the Recently checked list.
