# W-020 — The date filter judges TBC events by last edition's date

`priority: 2` · `effort: S` · `area: services` · `deploy: batched`
`source: scraper IDEAS.md 2026-09-05 "ANSWERED for indie-runners-web" (quoted below); AUDIT_20261021T0828 F1/F9; confirmed live in triage 2026-10-21`

## What is wrong

TBC rows are handled two ways in this app, and only one of them is
correct. **Admission** (`list_races`'s second `WHERE` arm) and
**ordering** (`main.py:232-239`, `_sort_date`) both use
`occurrence_year` + expected month. **The date filters do not.**
`date_from` / `date_to` compare `sort_key` (`race_service.py:164-171`):

```python
sort_key = func.coalesce(
    Race.race_date,
    func.make_date(Race.occurrence_year..., coalesce(expected_month, 12), 1),
)
```

The comment above it says the fallback is "for TBC rows". But a TBC row
usually **has** a `race_date`, inherited from the previous edition, so
for those rows the fallback never runs. The scraper's contract, measured
there 2026-09-05:

> **`occurrence_status = 'tbc'` means "this event recurs, we know roughly
> when, we do not know the day". Its `race_date` is LAST edition's date,
> inherited, and is not a claim about the upcoming one.**

Today the view carries **373 such rows across 96 events** (audit F1/F9).

## Evidence — live, 2026-10-21

TBC tiles on `https://indierunners.co/` and how the filter treats them:

```
(no filter)           Comrades Marathon (June 2027), Athens Half Marathon (March 2027),
                      Plaenterwaldlauf (Feb 2027), Monaco Run (Feb 2027), Valentislauf (Feb 2027)
date_from=2027-01-01  Athens Half Marathon, Monaco Run           <- 3 events expected in 2027 dropped
date_to=2026-12-31    all five                                  <- 5 events expected in 2027 kept
```

Monaco is the one that looks right by accident. Its inherited date is
2026-02-14 (scraper note), so `date_to` keeps it for the wrong reason.

**Corrected in triage:** this ticket was first written as "TBC sorts to
the top of the index". That was wrong. `main.py` re-sorts in Python with
a TBC-aware key, so the SQL `ORDER BY` on `sort_key` only decides row
order before grouping. The ordering is fine.

## Acceptance

1. With `date_from` / `date_to` set, a TBC row is judged by
   `occurrence_year` + expected month (December if null, as `_sort_date`
   does), **whether or not `race_date` is set**. Non-TBC rows are
   unchanged.
2. Re-run the two queries above. Comrades, Plaenterwaldlauf and
   Valentislauf appear with `date_from=2027-01-01`. None of the five
   appear with `date_to=2026-12-31`.
3. Verified in the browser, anon and signed-in.
4. **Say whether the SQL `ORDER BY` should use the same key.** It does
   not affect the index today. Name any other caller of `list_races`
   for which it does.
5. Changelog entry with the reasoning. The wrong belief is that "a TBC
   row has no `race_date`, so `coalesce` falls through".

## Out of scope

- **Admission** (the `WHERE` arms) and `_sort_date`. Both are already
  right.
- **W-012.** Blocked, and a different grain question.
- **Month granularity.** A TBC event expected in "February 2027" counts
  as 2027-02-01. That is the existing convention, kept.
- `core.*`. The inherited date is the scraper's documented contract, not
  a bug.

## Review — 2026-10-22 (PM)

Branch `fix/tbc-date-filter` at `ee9052c`.

**Sound.** `filter_key` judges a `tbc` row by its expected date and
leaves every other row on the old key. The admission arms and
`_sort_date` are untouched, as scoped. Acceptance 4 is answered with a
reason: `ORDER BY` stays on `sort_key` because only it orders an
event's races for first-see, and `main.py:180` is the only caller and
re-sorts in Python. The changelog names the wrong belief and the cost
(53 of 167 qualifying TBC events admitted by `date_from`, 161 where 1
qualifies by `date_to`). The five named events were checked in both
tiers. The comparison against master's `list_races` (same non-TBC event
sets under three filters and none) is better evidence than the ticket
asked for. Docs: 61 lines. Merges cleanly.

**The first-see finding is honest and correctly scoped out.** Non-TBC
rows get the same predicate value, but a different expression changes
the plan, so tied rows reorder. That nondeterminism predates this
branch. Filed as **W-029**.

**R1 — ARCHITECTURE now contradicts itself in the bullet this branch
edited.** Line 225 still says "the WHERE / ORDER BY / date-filter all
use `COALESCE(race_date, make_date(…))` so TBC rows sort and filter
alongside confirmed ones by their expected-month-start". Line 226, the
new text, says the date filters judge `tbc` rows by expected month even
when `race_date` is set. The first sentence is the wrong belief this
ticket's changelog names, still stated as fact one line above the
correction. (The admission arm never used the `COALESCE` either: it is
`race_date >= yesterday` or a bare `make_date`. So that sentence was
already overstated.) **Unblocks:** line 225 says what each of the three
uses now, or points to 226. No code change.

**Not verified:** I did not run the branch. The figures (53/167,
161/1, 174/41/49/215, 5–24) are the developer's. Month granularity is
unchanged by design.

**VERDICT: BLOCKED — R1**

## Re-review — 2026-10-22 (PM)

R1 is resolved at `2f5e5e5`. ARCHITECTURE line 225 now says what each
use takes: a `tbc` row is admitted and date-filtered on its expected
month even with an inherited `race_date`, and only `ORDER BY` uses the
`COALESCE`. Checked against `race_service.py`. It also drops the old
overstatement about admission. Docs-only change. Docs: 62 lines.
Merges cleanly.

**Not verified:** as in the first review. The production prediction is
`docs/ROUTED_CHECKS.md` entry 5.

**VERDICT: APPROVED**
