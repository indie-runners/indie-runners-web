# W-012 — A finished event vanishes the day after its last race

**Priority:** 2 · **Effort:** M · **Area:** services · **Deploy:** batched
**Source:** `docs/IDEAS.md` 2026-08-28 — Paulo, flagged **high priority**

## What is wrong

The defect is not "the retention window is one day instead of three." It
is that **the window is applied to the wrong grain.** The index is an
event listing; the filter that decides what appears on it is a *race*
filter, applied in SQL before the rows are grouped into events. The unit
the user sees and the unit the visibility rule operates on are not the
same thing, and every symptom below follows from that.

`app/services/race_service.py:157` and the `WHERE` at `:173-189`:

```python
yesterday = date.today() - timedelta(days=1)
...
stmt = select(Race).where(
    or_(
        and_(
            Race.race_date.isnot(None),
            Race.race_date >= yesterday,
        ),
        ...
```

So a race is kept while its own date is yesterday or later. An event is
present on the index only for as long as *some* race of it survives that
test — which for a single-day event means it disappears about a day after
it happens, and Paulo wants three.

**The subtler half, and the reason this is `M` and not `S`.** Because the
filter runs per race, a multi-day event that is *partly* past is already
being served with its early races missing. The grouping loop below builds
`distances`, `formats`, `cutoffs` and `race_date_end` from whatever rows
survived the `WHERE` — so on Aug 2, an event running Aug 1–3 renders with
its Aug 1 races silently absent from the tile. `race_date_end` is computed
at `:246-250`, *after* the filter, from the surviving rows only. It is
therefore both the value this ticket needs and a value the current filter
can corrupt. Any fix that keeps retaining per race inherits this bug.

## Evidence

`docs/IDEAS.md`, quoted in full because it carries the boundary:

> An event should stay visible after it is over, not disappear the moment
> it finishes. In his words: if an event's last race started **August 1st**,
> it should still be there through **August 3rd**, and by **August 4th** it
> should no longer appear. Recording the example rather than the phrase
> "three days after" on purpose — the two do not quite agree, and the dates
> are the tighter statement, so whoever specs this inherits the boundary
> and not the ambiguity.
>
> Note the key is the event's **last** race, not its first. An event whose
> races run Aug 1–3 is not "done" on Aug 1.

**The example is the specification.** "Three days" and the dates disagree
by one — Aug 1 through Aug 3 inclusive is a two-day tail, not three — and
where they disagree, the dates win. Written as a rule:

```
visible  while  today <= last_race_date + 2 days
gone     when   today >= last_race_date + 3 days
```

Check it against Paulo's own case: last race Aug 1 → visible Aug 1, 2, 3;
absent Aug 4. That is the requirement.

## STEP 1 HAS BEEN RUN, AND IT STOPS THE TICKET (PM, 2026-10-21)

**The query below was wrong, and its "rows come back" branch was the
wrong answer.** Rows do come back: 373 of them. All 373 are `tbc`. They
are kept by the view's first arm because they are TBC, not because they
are recent. The view definition (`pg_get_viewdef`, AUDIT_20261021T0828
F1):

```
WHERE occurrence_status = 'tbc'::text
   OR race_date IS NULL
   OR race_date >= CURRENT_DATE;
```

```
… WHERE race_date = current_date - 1;                          {'count': 0}
mv WHERE race_date < current_date AND occurrence_status <> 'tbc'
                                         {'mv_past_non_tbc_rows': 406, 'events': 103}
```

So a non-TBC race is in the view on `D` only. `D+1` and `D+2` cannot be
built in this repo. The corrected gate is the same query with
`AND occurrence_status <> 'tbc'`. **Do not re-run it; this is the
result.** The ticket's own stop branch applies. The request to retain
non-TBC rows through `D+2` goes to the scraper's `docs/IDEAS.md`, and nothing here
starts until the view changes. When it does, re-run the corrected gate,
then the ticket below applies unchanged. W-016 no longer waits on it.

## Step 1, as originally written

**Does `core.v_denormalized_event_data_upcoming` still carry rows whose
`race_date` is in the past?** Everything the index reads comes through
that view, it is scraper-owned, and its name says *upcoming*. If the view
drops a race once it is past, **no filter change in this repo can retain
the event** and the fix is not here.

One query settles it:

```sql
SELECT count(*), min(race_date), max(race_date)
FROM core.v_denormalized_event_data_upcoming
WHERE race_date < current_date;
```

- **Rows come back** — the premise holds, do the ticket.
- **Zero rows** — **stop.** Do not widen the filter against a view that
  cannot supply the data; the result is code that looks like it works and
  retains nothing. Route the finding to `indie-runners-scraper/docs/IDEAS.md`
  with the query and its output **quoted inline**, `source: web-audit`,
  per `docs/roles/README.md`, and set this ticket `blocked` with that
  entry named in `notes`. This repo cannot fix `core.*`.

The idea's hunch is that rows are retained — the app's own `>= yesterday`
filter would have nothing to do otherwise. That is an inference from the
code, not a measurement. **Measure it before writing the filter**, and
mind the standing constraint: one session does DB-touching work at a time,
across both repos.

## Acceptance

1. **The dates, exactly.** An event whose last race is on day `D` appears
   on the index on `D`, `D+1` and `D+2`, and does not appear on `D+3`.
   Verify against Paulo's own case (last race Aug 1 → present Aug 3,
   absent Aug 4) using a real event in the corpus, naming which one.
2. **Last race, not first.** An event running Aug 1–3 is still present on
   Aug 4 (`D+1` from its Aug 3 finish). Verified against a real multi-day
   event, named in the close-out.
3. **A retained event retains all of its races.** The event page and the
   index tile for a partly-past event show its early races too — the
   distances list, the format badges and the cutoff set are the same as
   they were before its first race ran. This is the pre-existing bug
   described above; it is in scope because the fix either closes it or
   entrenches it.
4. **Verified in the browser, anon and signed-in.** The index is two-tier
   and it is easy to check only the tier you are logged into.
5. **The TBC arm still works.** Events with `occurrence_status = 'tbc'`
   and no `race_date` are matched by the second arm of the `WHERE`, which
   this ticket does not touch. Confirm a TBC event still lists.
6. **Named in the changelog with the reasoning**, per `docs/PLAN.md`
   close-out: the wrong belief (a race-grained window is an event-grained
   window), what it cost, the new belief, the evidence.

## Notes for whoever picks this up

The obvious implementation — relax the `WHERE` to `race_date >= today - 3`
— satisfies acceptance 1 for single-day events and **fails 2 and 3**. The
grain is the whole ticket: the decision is per event, on `max(race_date)`,
and the rows must all survive for the tile to be right. Whether that lands
as a window function / correlated subquery in SQL or as a wider fetch
filtered after grouping is the developer's call — but **name the choice
and why**, including what it costs at 1724 rows, because a post-grouping
filter means fetching rows the query used to exclude.

Watch the ordering key too: `sort_key` (`:161-170`) coalesces
`race_date` with a synthesised first-of-month for TBC rows and is used by
`ORDER BY` and by the user's date filters. A finished event that is
retained still sorts by its own date — i.e. it sorts into the past, at the
top of an ascending list. **Decide where a finished event belongs in the
order and say so**; acceptance 1 is about presence, and presence at the
top of the page is a different product than presence at all. If the answer
is not obvious from the mockups, say what you chose and why rather than
letting `ORDER BY` decide silently.

## Out of scope

- **Any visual treatment for a finished event** — a "finished" badge, dimming,
  a separate section. This ticket makes the event *present*; how a past
  event should look is a design question nobody has asked yet, and pulling
  it in makes a services ticket a template ticket. If the developer finds
  that presence alone reads as broken, that is a `docs/IDEAS.md` note, not
  a widening.
- **The event detail page's own reachability.** `/events/{slug}/{year}`
  is not filtered by `list_races` and is out of this diff.
- **The TBC arm of the `WHERE`.** Untouched.
- **Retention anywhere but the index** — profile pages, crew pages, any
  other caller of `list_races` gets whatever falls out of the shared
  change, and reasoning about each surface separately is not this ticket.
  Name in the close-out which other callers exist and what they now do.
- **Changing what `core.*` serves.** Not this repo's, ever. If step 1
  fails, the ticket routes and stops.
