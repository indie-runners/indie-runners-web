# W-016 — The tile shows one race's price and calls it a floor

`priority: 2` · `effort: S` · `area: services` · `deploy: batched`
`source: docs/IDEAS.md 2026-09-03 (Paulo), premise corrected in triage`

## What is wrong

**The ask, in Paulo's words: the tile should show the range of the
event's race prices.** If the cheapest race is 20 and the dearest is 80,
it should read `20 - 80€` rather than one number. That is the whole
request and this ticket is scoped to it.

Underneath it is a defect, and it is the reason this is `p2` rather than
a cosmetic `p4`. **The tile is not showing the lowest price — it is
showing whichever race sorted earliest by date.**
`RaceService.list_races` takes `registration_price` and `price_currency`
in the **first-see** branch of the grouping loop
(`app/services/race_service.py:242-243`), while the template renders that
value with a trailing `+`:

```jinja
{% set price_label = race.price_currency ~ ' ' ~ race.price ~ '+' if (race.price and race.price > 0) else ('Free' if race.price == 0 else '—') %}
```

`app/templates/partials/race_tile.html:4`. The `+` asserts a floor —
"from 20". The number is not a floor. **On an event whose earliest race
is the 100km ultra, the tile presents the dearest price as a minimum.**
That is wrong data rendered to an anonymous visitor, which is priority
band 2 on `docs/roles/pm.md`'s scale, and it is wrong today regardless of
whether a range is ever built.

**This is a known bug class in this file, not a new discovery.**
`docs/ARCHITECTURE.md` records it twice under the read model — a
race-level field read off `rows[0]`, once for the hero-image terrain and
once for the format filter. The grouping loop already does the right
thing for `distances`, `formats` and `cutoffs`, each collected on every
row with a comment saying why (`race_service.py:253-262`). Price is the
one field that was left on first-see.

## Evidence

The first-see block, `app/services/race_service.py:242-243`:

```python
                    "price": r.registration_price,
                    "price_currency": r.price_currency,
```

Ten lines below it, the pattern this ticket applies to price
(`:253-256`):

```python
            # Collected on every row, not only first-see: format lives on the
            # individual race, and the first row seen is the earliest-dated
            # one, which frequently has no format while a later sibling does.
            events[eid]["formats"].update(parse_race_formats(r.race_format))
```

The comment already states the general case. It is true of price for the
same reason.

## The rules this ticket settles

**Free races — Paulo delegated this call and it is taken here.** The
template already renders `price == 0` as `Free`, so a free floor reads
**`Free – €123`**, not `€0 – €123`. Reason: it keeps the vocabulary a
visitor already sees on single-price tiles rather than introducing a
second rendering of zero.

**Not discretionary, and the trap in this ticket: `0` and `NULL` are
different and must stay different.** The template already branches them —
`0` is `Free`, missing is `—`. `NULL` means *unknown*, not free. **A row
with no price is excluded from the range entirely; it is never the
floor.** Rendering an unpriced race as a `Free` lower bound would invent
a claim the source data does not make, which is the same defect this
ticket exists to remove.

**Mixed currency within an event.** `price_currency` is race-level and is
taken on first-see alongside the price, so a range could silently span
two currencies. The rule: **a range is rendered only when every priced
row of the event shares one currency.** Where they disagree, fall back to
a single value rendered *without* the `+` — never a converted or mixed
range. One query settles how often this happens and it belongs to
whoever picks this up, not to triage (the connection budget rule):

```sql
SELECT count(*) FROM (
  SELECT event_id FROM core.v_denormalized_event_data_upcoming
  WHERE registration_price IS NOT NULL AND price_currency IS NOT NULL
  GROUP BY event_id HAVING count(DISTINCT price_currency) > 1
) t;
```

**Report the number in the close-out.** If it is zero the fallback is
dead code that still belongs there; if it is large the rule is worth
revisiting.

## Acceptance

Every case below is a tile rendering, checked in the browser:

1. **A range.** An event whose races differ in price renders
   `min – max`, and the trailing `+` is **gone**. Name the event checked.
2. **All races the same price** renders the single value (`20€`), not
   `20 – 20€`.
3. **A free race alongside priced ones** renders `Free – €123`.
4. **All races free** renders `Free`, as today.
5. **All races unpriced** renders `—`, as today.
6. **Unpriced mixed with priced** renders the range over the priced rows
   only — the unpriced row does not become the floor.
7. **Mixed currency** renders the single-value fallback without the `+`,
   per the rule above.
8. **Verified anon and signed-in.** The index is two-tier.
9. **Changelog names the wrong belief** — "the tile's price is the
   event's cheapest race" / "the `+` marks a floor" — what it cost, and
   the evidence.

## Out of scope

- **The event detail page's price display.** Different surface, not the
  tile Paulo asked about. If it has the same first-see defect, that is a
  `docs/IDEAS.md` note, not a widening of this ticket.
- **Any currency conversion.** Named explicitly because it is the
  tempting fix for the mixed-currency case and it fabricates a number.
- **A price filter**, or anything in the advanced filter panel.
- **Changing the `{currency} {price}` format itself** — decimals,
  symbol placement, thousands separators. Only the range and the `+`.
- **`core.*`.** `registration_price` and `price_currency` are correct at
  source; this is entirely a read-side grouping defect.

## Review — 2026-10-22 (PM)

Branch `fix/tile-price-range` at `081b57d`.

**Sound.** The fix is the per-row pattern the ticket pointed at, ten
lines from its siblings. `0` and `NULL` stay distinct. Rows arrive in
`sort_key` order (`race_service.py:208`), so "earliest-dated" in the
fallback is true. Nothing else reads the tile price: `event.html` reads
per-race rows, and `static/js/script.js`'s `+` is the mockup page.
The changelog names the wrong belief, the cost (32 of 90 tiles above
their floor, 11 showing `—` with priced races), the new belief and the
evidence. All seven cases are named tiles in both tiers. Docs: 70 lines.

**The call the ticket did not settle is right.** Before this change,
a positive price with NULL currency rendered as `None 77.95+`. Excluding
it is better than inventing a unit, and the developer flagged that it
changes 6 tiles. The source defect is routed to the scraper (below).

**R1 — `price` is documented as the floor, and under mixed currency it
is not.** `app/schemas/race.py:24` says `# lowest price across the
event's races`, and ARCHITECTURE says "Price is now a range over every
priced race (`price` the floor …)". In the mixed-currency branch,
`price` is the **earliest-dated** positive price, not the lowest, and
there is no range. Zero events today, so no tile is wrong. But this is
the claim the next caller will build on. A price sort or filter (named
out of scope here, so plausible next) would read `price` as a floor and
be wrong exactly where the ticket said a floor is a lie. **Unblocks:**
both sentences say what `price` is in the mixed-currency case. Two
lines, no code change.

**Not verified:** the mixed-currency branch has never rendered (0
events). It was read, not run, and I read it too. I did not re-run the
tiles; the review relies on the named renders in the changelog. A tie
in `sort_key` between two currencies on the same date would pick
arbitrarily. That is unreachable today and acceptable.

**Routing:** the DEV_NOTES entry (19 priced rows, NULL currency) is
`core.*` and goes to the scraper's `docs/IDEAS.md`.

**VERDICT: BLOCKED — R1**

## Re-review — 2026-10-22 (PM)

R1 is resolved at `7f9035c`. The schema comment and ARCHITECTURE now
both say that under mixed currency `price` is the earliest-dated
positive price, not a floor, and there is no range. No code changed, so
the first review's findings stand. Docs: 71 lines.

**Not verified:** as in the first review. The branch was not run by the
PM. The mixed-currency branch has never rendered. The prediction for
production is `docs/ROUTED_CHECKS.md` entry 4.

**VERDICT: APPROVED**
