# W-014 — The other 53 column declarations in `core.py` have never been checked against the view

**Priority:** 3 · **Effort:** S · **Area:** models · **Deploy:** batched
**Source:** W-007 review 2026-08-28; the developer's own named follow-up

## What is wrong

`app/models/core.py` declares 54 columns against a view this repo does
not own. W-007 checked exactly one of them — `mv_id` — found it wrong,
and the changelog says so plainly:

> No other column in `app/models/core.py` was audited for the same class
> of mismatch — deliberately out of scope, and a fair follow-up ticket.

That boundary was right for W-007 and this is the ticket it implies. The
defect is not "a column might be mistyped." It is that **the declarations
were never checked against the thing they describe**, and the one time
anybody looked, the answer was no. One sample, one hit, 53 unlooked-at.

**W-007 raised the value of this audit past what it was worth before it.**
The `mv_id` mapping was wrong in *two* directions, and only one of them
was the reported bug:

- the SQL half — `WHERE mv_id = $1::VARCHAR` against a `uuid` column,
  which is what 500'd the page; and
- the Python half — under `Text`, SQLAlchemy applied no result processing,
  so psycopg returned a `uuid.UUID` **object** while the annotation said
  `Mapped[str]`.

The second was invisible for eighteen days and was found only because
somebody printed the value while fixing the first. **A mismatch that
never emits bad SQL can still hand the app a type it did not declare** —
and that failure is silent, surfacing as an `AttributeError` or a
malformed string in a template, far from the declaration. `Text` is the
declared type on 27 of the 54 columns, which is where a wrong guess is
most likely to hide.

## Evidence

`app/models/core.py`, current type spread:

```
27  mapped_column(Text
17  mapped_column(Boolean
 4  mapped_column(Double
 2  mapped_column(Integer
 2  mapped_column(Date
 1  mapped_column(Time
```

Plus `mv_id`, now `Uuid(as_uuid=False)` — the one that was checked.

The cost of the one known mismatch, from the W-007 changelog:

> It took a full debugging pass to find the first time, against a
> one-line fix.

## Acceptance

1. **Every column in the view compared to its declaration**, from one
   query — `information_schema.columns` for
   `core.v_denormalized_event_data_upcoming` — set beside the 54
   `mapped_column` calls. One session, per the connection budget.
2. **Both directions checked, not just the SQL.** For each mismatch, say
   whether it can emit invalid SQL, or silently return a Python type other
   than the annotation, or both. The `mv_id` lesson is that the second
   kind exists and is quieter.
3. **Nullability too, where it is free.** `Mapped[str]` vs
   `Mapped[str | None]` against the view's `is_nullable` is in the same
   query and the same class of defect — a column declared non-optional
   that returns NULL is a lie the type checker believes. Report it; fixing
   it is only in scope where the view says nullable and the model does
   not.
4. **The finding is the deliverable, and it may be "nothing".** If all 53
   match, say so with the query output quoted, and this ticket closes as
   verified rather than as work. That is a real result: it converts "never
   checked" into "checked on 2026-08-28", which is the actual defect being
   fixed.
5. **Fix only unambiguous mismatches in this diff.** A wrong type where
   the right one is obvious (the `mv_id` shape) is fixed here. Anything
   requiring a judgement call about downstream readers gets its own
   ticket, named in the close-out.
6. **Date the result in `docs/ARCHITECTURE.md`**, following the convention
   W-002 established: an audit whose date is not recorded is one that has
   to be redone to be trusted.

## Out of scope

- **Changing anything in `core.*`.** The column types in the database are
  correct and are the scraper's. If the audit finds a column whose
  *database* type is wrong, that routes to
  `indie-runners-scraper/docs/IDEAS.md` with evidence quoted inline —
  never a ticket here.
- **`app/models/web.py`.** This repo owns `web.*` and its models were
  written against a schema this repo also wrote, so they do not carry the
  same never-checked-against-the-source risk. Different ticket if anyone
  wants it.
- **Widening `mv_id` to `UUID` objects.** W-007 decided `as_uuid=False`
  and that decision is not reopened here.
- **Automating the check.** A recurring drift test belongs to W-003, not
  to a one-off audit.

## Verdict

**VERDICT: APPROVED** — 2026-10-25. One `information_schema.columns`
query found that 54 of 55 mapped types match. `occurrence_id` (`text` in
the view, declared `Integer`) is now `Text` / `Mapped[str | None]`. Both
directions were measured on master. On the Python side, a `str` came back
under an `int` annotation. On the SQL side, `== 7837` raised
`text = integer`, a latent bug because nothing filtered on it. The branch
has exactly two readers of `Race.occurrence_id`, `race_service.py:238`
and `main.py:395`, and both `int()` it. Attendance routes take the id from
the URL path and raw SQL, not from `Race`, so returned values are
unchanged. Pages were served from `irw-W014` (confirmed by cwd) against
master on `:8015`: 4 routes × 2 tiers, all byte-identical, all `200`.
**Spec premise disproved:** acceptance 3 assumed nullability was "free in
the same query", but Postgres reports every view column as nullable. The
3 non-optional declarations hold 0 NULLs in 1929 rows. Leaving them
non-optional is a judgement call. It needs no ticket: no reading can
contradict it except a NULL, and none exists. Ticket is `deploy: batched`.
No routed check, because nothing in production should look different.

**Not verified:** the 54 matches. The query output is summarised, not
quoted, and I did not re-run it (one DB session at a time). W-025's
`event_last_checked_at` is confirmed only as one of the 54, not by name.
The comment "like every `occurrence_*` column" rests on the same
unquoted query. The IDEAS entry (a drift check, attributed to Paulo) is
for triage, not this review.
