# W-102 — "← All events" on an event page drops the filters the user set

`priority: 3` · `effort: S` · `area: templates` · `deploy: batched`
`source: docs/IDEAS.md 2026-11-04 (Paulo)`

## What is wrong

A runner filters the index, opens an event, and clicks "← All events".
The link is a plain `/`, so they land on the unfiltered list. The
filtered list already has its own URL, because the filters are a `GET`
form, but neither the tile nor the back link carries it.

## Evidence

Paulo, from `docs/IDEAS.md`:

> once the user uses the filter, checks one race, and decides to come
> back, clicking "← All events" shows all the tiles again. Is this
> correct, or should people be expected to hit the browser's back button
> to get their filters back?

```
app/templates/index.html:10          <form method="get" action="/" id="filter-form">
app/templates/partials/race_tile.html:20  <a class="tile-link" href="/events/{{ race.event_slug }}/{{ race.occurrence_year }}" ...>
app/templates/event.html:23          <a href="/" class="back-link">← All events</a>
```

The answer to Paulo's question: no. A link labelled as a way back should
go back to what the runner left. The browser's back button is not enough:
a shared link or a new tab has no history.

## Acceptance

1. Filter the index (say country and a distance range), open a tile,
   click "← All events": the index shows the same filters applied and
   the same tiles.
2. No filters set: the link is `/`, as now.
3. An event page opened directly (pasted URL, new tab, a crew hub or
   profile link): the link is `/`.
4. The back link can only ever lead to the index on this site. Whatever
   carries the filter state is not an open redirect.
5. The event page's canonical URL, if it has one, does not change with
   the filters. Both tiers render.

## Out of scope

- Scroll position on return.
- The other three "← All events" links (`profile.html`, `settings.html`,
  `event_not_found.html`). They do not follow a filtered list.
- How the state is carried (referrer or a query parameter): the
  developer names the choice and why.

## Verdict

**VERDICT: APPROVED** — 2026-11-08, re-review at `4ecf595`. R1 resolved in
`2321937`: the changelog now says a URL pasted into a new tab gives `/` and a
tile opened in a new tab keeps the filters. No code changed since `55971cf`;
docs 56/100. Ticket is `deploy: batched`. Routed check 56 stands as written.

**Not verified:** unchanged from below: the finished-year 302, and the
production Host/Referer pair (check 56).

Earlier, superseded:

**VERDICT: BLOCKED — R1** — 2026-11-08, branch `fix/back-link-keeps-filters`
at `55971cf`.

The code holds. Only the query is copied, behind a literal `/?`, so the
link cannot leave the index: `//evil.example`, a foreign host and a
`"><script>` query were all run. No HTML response carries a `Cache-Control`
(only `/static/` does), so no cached page can hand one runner's filters to
another. One ticket, both tiers, docs 55/100. Choosing the referrer over a
query parameter is argued, and the one-hop limit is named in the code and in
DEV_NOTES.

**R1 — the changelog says "new tab" gives `/`, and the common case does
not.** 1.9.71: "The referrer falls back to `/` in exactly those cases
(pasted, new tab, profile, crew hub, another site)." A tile opened in a new
tab from the filtered index (middle-click, ctrl/cmd-click) still sends
`Referer`, so that tab's back link keeps the filters. That behaviour is
right; the sentence is wrong, and "exactly" makes it a rule someone will
inherit. The phrasing came from this ticket's acceptance 3, which meant a
URL pasted into a new tab. **Unblocks:** change "new tab" to "pasted into a
new tab" (or say a tile opened in a new tab keeps them). No code change.

**Not verified:** the 302 from a finished year to the next (browsers keep
`Referer` across a redirect; nobody ran it here). The production Host and
Referer pair behind Cloud Run's domain mapping: everything ran against
`localhost:8000`. Routed check 56 settles that.
