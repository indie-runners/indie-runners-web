# W-002 — ARCHITECTURE's core read model reasons from ~9-week-stale numbers

`priority: 2` · `effort: S` · `area: docs` · `deploy: batched`
`source: audit baseline 2026-08-28` · re-confirmed by
`exports/reports/AUDIT_20260828T0812.md` (F1)

## What is wrong

`docs/ARCHITECTURE.md` states the core read model's size as current fact —
"currently 967 rows across 233 events". Measured 2026-08-28 it is **1724 rows
across 356 events**. The corpus has roughly doubled; the document has not moved.

The defect is not the wrong numbers. It is that this file is the repo's stated
home for *why* a decision was made, and it quotes **undated absolutes** in the
same breath as the reasoning built on them. A reader cannot tell which sentences
are a durable conclusion and which are a measurement with a shelf life. The next
person sizing a change against "233 events" reasons about a database 53%
smaller than production.

The auditor deferred the fix to the PM — re-measure, or stop quoting absolutes?
**Answer: both, separated.** Re-measure with a `measured` date attached, and
keep the grain *conclusions* in sentences that do not depend on a count. A
number that carries a date goes stale honestly; one that says "currently" lies.

## Evidence

The audit re-measured against `core.v_denormalized_event_data_upcoming`:

```
{'rows': 1724, 'events': 356}
```

`docs/ARCHITECTURE.md:39`:

```
**The grain is one row per race, not per event** — currently 967 rows across 233
events, each of which has exactly one live occurrence.
```

`docs/ARCHITECTURE.md:52-53`:

```
**`event_location` is dead — NULL on all 967 rows.** The populated column is
`race_location` (913 of 967 rows, 221 of 233 events), and it is *race*-grained:
```

`docs/ARCHITECTURE.md:84`:

```
  empty affordance: `short_description` is on 229 of 233 events, `race_format`
```

Re-measured 2026-08-28, the same three claims read:

- `event_location` populated on **0 of 1724** rows — the dead-column claim
  **still holds**.
- `race_location` null on **129 of 1724** rows, i.e. populated on **1595**.
- `short_description` null on **10 rows across 3 events** — present on
  **353 of 356 events**, not 229 of 233.

The audit's own conclusion, and I agree with it: *"the conclusions in that
document survive re-measurement — nothing built on them is wrong today."* This
is a documentation-integrity ticket, not a correctness one. That is why it is
p2 and not p1.

## Scope beyond what the audit measured

The audit checked three claims. The section carries more undated counts that
were not re-measured and are in the same position — do not fix only the three
that were quoted:

- `docs/ARCHITECTURE.md:39` — 967 rows / 233 events
- `:52-53` — `race_location` 913 of 967 / 221 of 233; "49 events carry more
  than one value"
- `:57` — "reimplementing that choice in SQL diverged on **11 events**"
- `:61` — "163 events carry more than one distance, 41 more than one cutoff,
  21 more than one terrain"
- `:84` — `short_description` 229 of 233, `race_format` on 70, `cutoff_time`
  on 57

## Acceptance

- Every count in the "one row per race" section is either re-measured against
  production today, or removed in favour of the claim it supports.
- Numbers that stay carry a **measured-on date** and are not phrased as
  "currently".
- The **grain claims are checked, not just the denominators.** Specifically,
  confirm as still true after the corpus nearly doubled:
  - `event_location` still NULL on every row.
  - `race_location` still race-grained — some events still carry >1 value.
  - `short_description` still event-grained: **zero** events carry more than
    one distinct value across their races. This is the one that matters most —
    `RaceService` and PLAN.md ticket 2 both read it off a single row, and if it
    stopped holding, that is a real bug and not a docs ticket. Say in the
    changelog which of these were re-verified.
- The changelog entry names the wrong belief: not "the numbers were old" but
  "an undated absolute in an architecture document is a measurement pretending
  to be a decision".
- `docs/CHANGELOG.md` version bumped.

## Out of scope

- **Fixing anything the re-measurement turns up in `core.*`.** If a grain claim
  has stopped holding because of scraper-side data, that is a finding for
  `indie-runners-scraper`'s `docs/IDEAS.md` with the evidence quoted inline and
  `source: web-audit` — not work in this repo. If it has stopped holding and
  **this app misreads it**, stop and come back for a new ticket; do not fix code
  under a docs ticket.
- **Re-measuring the rest of `ARCHITECTURE.md`.** This ticket is the core read
  model section. The `web.*` tables and static-assets sections are not in scope.
- **Setting up any scheduled re-measurement.** Tempting and out of scope; the
  dated-number convention is the fix here.
- **Tickets A, B and F**, referenced in that section. Untouched.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-011** — 2026-08-28. Merge now.

Both halves of the fix landed, and separated as the ticket asked: every count
in the section is re-measured and carries `measured 2026-08-28`, and the
*conclusions* were rewritten to stand without the counts beside them. The
"currently" phrasing is gone. The changelog names the belief correctly — an
undated absolute is a measurement pretending to be a decision — rather than
"the numbers were old", which was the available shortcut.

**Verified independently, not accepted from the changelog.** Every figure in
the diff was re-run against `core.v_denormalized_event_data_upcoming` in a
separate read-only session during this review, and **all sixteen reproduced
exactly**: totals 1724/356, 1–18 races per event averaging 4.8, `event_location`
0 of 1724, `race_location` 1595 rows / 342 events with 90 multi-value events
(103 null-sensitively), `short_description` 0 multi-value events on both the
plain and the NULL-sensitive test with its 10 NULL rows across 3 events,
race-level disagreement at 278/105/56, coverage at 353/90/149.

Three judgements worth recording as good ones:

- **The NULL-sensitive re-run of `short_description` was not asked for and is
  the best thing in the branch.** A plain `count(DISTINCT)` ignores NULLs, so
  an event with the description on one race and absent on another would have
  passed the test the ticket literally specified. That is the exact shape of
  defect this repo's review process exists to catch, and the developer caught
  it in their own work.
- **The "11 events" number is kept, dated, and labelled as un-re-measurable.**
  It is a one-off experiment's result, not a corpus property. Provenance
  checked in review: `git log -S` puts it in `f947108`, 2026-08-10, against the
  then-233-event corpus, exactly as claimed. Deleting it would have discarded
  the evidence behind the conclusion; reprinting it undated would have been the
  original defect again.
- **The self-disagreement was flagged, not silently fixed.** Widening a docs
  ticket to the whole file is precisely what an out-of-scope list is for.

**Follow-up W-011, and it is not a condition.** `ARCHITECTURE.md:211` restates
`race_format` coverage as "roughly 70 of 236" — the developer flagged this in
`DEV_NOTES`. Found in this review and **not** flagged: `:209` carries
`cutoff_time` at "57 of 234", the same defect one paragraph earlier. W-011
covers both, with the measured replacements (90 of 356, 149 of 356) already in
its notes so no further DB session is needed. Both lines are in the services
section, which this ticket scoped out correctly.

**Not verified:**

- **The other event-grained columns are taken on the changelog's word.** It
  reports 0 violations for `event_display_name`, `event_country_code`,
  `event_website_url`, `event_type` and `occurrence_year`. I re-ran only
  `short_description` and `race_location` null-sensitively. No reason to doubt
  the rest — the two I checked reproduced exactly — but they are unconfirmed.
- **`occurrence_*` is a wildcard in the table and was verified as
  `occurrence_year` only.** If a gap exists it is in `occurrence_status` or
  `occurrence_expected_month`, both of which the index's TBC handling reads.
  Cheap to close and worth doing at the next sweep rather than blocking here.
- **No rendered surface was checked, and correctly so.** The diff is prose —
  no code, no template, no query — so there is nothing that could render
  differently. The changelog says this in as many words rather than claiming a
  browser check that would have meant nothing.
- **Nothing enforces the convention going forward.** The next number added to
  this file can be undated and nothing will notice. Left as a convention
  deliberately (scheduled re-measurement is out of scope in both W-002 and
  W-011). **For the auditor:** whether the dated-number convention actually
  held is a question for a future sweep, not for this review — the honest test
  is what the file looks like after the next few tickets touch it.
- **The measurements are a point-in-time snapshot** taken the same day as the
  branch. That is the nature of the fix, and the date on each number is what
  makes it honest rather than a defect.

Ticket is `deploy: batched` — nothing here reaches production on its own.
