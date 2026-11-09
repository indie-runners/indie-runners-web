# W-007 — `Race.mv_id` is mapped as `Text` but the column is `uuid`

`priority: 2` · `effort: S` · `area: models` · `deploy: batched`
`source:` `exports/reports/20260808_new_tickets_from_bugs.md`, Ticket F —
**that file is gitignored**, so every fact it carries is quoted below. It
never reached the board; this ticket is that omission being corrected.

## What is wrong

`core.v_denormalized_event_data_upcoming.mv_id` is a `uuid` column.
`app/models/core.py:17` declares it:

```python
mv_id: Mapped[str] = mapped_column(Text, primary_key=True)
```

The defect is not the wrong type annotation. It is that **the workaround
shipped and the landmine did not get defused.** A production 500 was
diagnosed, traced to this mapping, and then routed around — and the
routing-around is now load-bearing, documented in a comment at the site of
the workaround rather than fixed at the site of the cause. The next
developer who commits the request session mid-render will hit the same
500, and the comment that would have warned them lives in a different file
from the one they are editing.

## Evidence

The mismatch is invisible on ordinary reads: nothing filters on `mv_id`.
It bites when SQLAlchemy issues a `WHERE mv_id = :pk` — which happens
whenever a `Race` is **expired and then re-accessed**. Postgres rejects it:

```
operator does not exist: uuid = character varying
LINE 3: ... WHERE ...mv_id = $1::VARCHAR
```

Quoted from Ticket F, which found it while building the 1.6.0 terrain heal:

> Found during Ticket D: an early version of `_heal_defaulted_terrain`
> committed on the request's session, which expired the in-flight
> `core.Race` rows, and the next attribute access on one 500'd the whole
> event page. Ticket D worked around it by committing on a separate
> Session — correct on its own merits, but the underlying landmine is
> still armed.

The workaround is in the tree today, `app/services/event_image_service.py:170-177`:

```python
# Committed on a short-lived Session of its own, NOT self.db. Committing
# the request's session expires every object it has loaded, including the
# core.Race rows the caller is still iterating; re-reading an expired
# Race triggers a load-by-PK that fails outright, because the view's
# mv_id is `uuid` while the model maps it as Text. A commit here would
# therefore 500 the page.
```

Blast radius, checked today — `mv_id` is read nowhere but its own
declaration and that comment:

```
app/services/event_image_service.py:175:        # mv_id is `uuid` while the model maps it as Text. A commit here would
app/models/core.py:17:    mv_id: Mapped[str] = mapped_column(Text, primary_key=True)
```

## Why p2 and not p5

Nothing is broken today, which argues for hygiene. Against that: the
failure mode is **a 500 on a page render, triggered by a change that has
nothing to do with this file**, and the diagnosis cost is high relative to
a one-line fix — it took a full debugging pass the first time. A latent
defect whose trigger is "someone edits unrelated code correctly" is not
hygiene. It is p2 with an `S` effort, which is the cheapest p2 on the
board.

## Acceptance

- `mv_id` is mapped as a UUID type — `Uuid(as_uuid=False)` or
  `postgresql.UUID(as_uuid=False)`. **Keep the Python-side value a
  string**: `Mapped[str]` is what the rest of the app assumes, and
  changing it to `UUID` objects is a wider change than this ticket.
- **The failure is reproduced before the fix and shown gone after.** There
  is no test suite (W-003), so this is the only evidence that exists.
  Force the expire-then-access path deliberately — load a `Race`,
  `session.expire_all()` (or commit on the request session), touch an
  attribute — and confirm it raises the `operator does not exist` error
  before, and does not after. Say in the changelog exactly what was run.
- **An event page renders correctly for both tiers**, anon and signed-in.
  The `Race` model is on the hot path of every page.
- The changelog entry names the wrong belief. It is **not** "the type was
  wrong". It is: *a defect that has been diagnosed and routed around is
  not a closed defect — the workaround is a record that the cause is still
  there.*
- `docs/CHANGELOG.md` version bumped.

## Out of scope

- **Removing the separate-Session commit in `_heal_defaulted_terrain`.**
  It is correct on its own merits — the docstring argues healing should be
  transactionally independent of the render, and that argument does not
  depend on this bug. Fixing the mapping does not make the workaround
  wrong. **Do update the comment at line 170-177** so it no longer
  describes an armed landmine as if it were current, but leave the code.
- **Auditing the rest of `app/models/core.py` for type mismatches.** A
  reasonable follow-up and a different ticket; this one is `mv_id`, which
  is the only column with a demonstrated failure.
- **Anything in `core.*`.** The column type is correct in the database.
  This is the app misreading correct data — fixed here, per the routing
  table in `docs/roles/README.md`.
- **W-003.** The temptation to write the first test here is real and the
  reproduction above is nearly one. Do not start a suite under this ticket.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-014, W-015** — 2026-08-28.
Merge now; neither follow-up is a condition.

The fix is one line and the reasoning around it is the reason this took a
review rather than a glance. Three things I checked rather than accepted:

- **The blast radius claim.** `grep` for `mv_id` across `app/` returns the
  declaration and one comment, on master and on the branch. Nothing reads
  it, so the mapping really is the whole surface.
- **`Uuid` is available at the pinned version.** `sqlalchemy.Uuid` is 2.0+;
  `requirements.txt:8` pins `>=2.0.0,<2.1`, installed 2.0.50. It imports.
  Worth checking because a fix that only works on the developer's
  interpreter is not a fix.
- **`as_uuid=False` is the right call, not the timid one.** `Mapped[str]`
  and every downstream reader assume a string. Widening to `UUID` objects
  would have been a larger change than a latent defect warrants, and the
  branch says so at the declaration instead of leaving it implied.

**The changelog is the standard 1.9.3 set, and it does something better.**
It names a wrong belief that is not about types at all — *that a defect
which has been diagnosed and routed around is a closed defect* — and the
evidence is the eighteen days the landmine sat armed with an accurate
seven-line comment sitting next to it. It also self-reports a second
mismatch nobody asked about: under `Text`, psycopg was returning a
`uuid.UUID` object while the annotation said `str`. Volunteering a
finding that makes your own diff look less complete is the behaviour this
review exists to reward, and it is what W-014 is built on.

**The verification is symmetric and that is the point.** Both scripts were
run against unfixed `master` *and* the branch, and the three page renders
were diffed byte for byte between two builds on ports 8011/8012. A
byte-identical result is the correct outcome for a change that alters the
SQL a load-by-PK emits and nothing a page renders — and the branch states
that as the claim rather than presenting "it still works" as a pass. The
anon page's small size was interrogated rather than assumed, by minting a
session cookie and confirming the missing bulk was the `locked-panel`
gate.

**Docs hygiene.** `CHANGELOG` 1.9.6 follows 1.9.5 correctly.
`ARCHITECTURE.md` updated in both places the old mapping was described —
including the static-assets section, where the heal's justification was
quietly load-bearing on the bug and now stands on its own merits.
`FILE_TREE.md` correctly untouched: `--diff-filter=ADR` is empty.

**The two follow-ups are the branch's own honesty, filed rather than left
as prose.** `W-014` is the column audit the changelog offered — worth
more after this ticket than before it, because the Python-side half proves
a mismatch can be silent. `W-015` answers the CRLF note's explicit
question to me: ticketed, because the artefact degrades the single-writer
rule, which is enforced by reading a diff.

**One process note, not a finding.** `status` was `wip` and `branch` was
set when I reviewed. Reviewing at `wip` was fine — Paulo asked directly —
but the flip to `review` is the developer's, and I have not touched
either column.

**Not verified:**

- **I did not re-run the reproduction or the byte-diff.** The evidence is
  symmetric and the one-session DB rule says that query belonged to the
  developer. I reviewed the reasoning and the artefacts, not a repeat run.
- **The OAuth round trip.** The signed-in tier was reached with a
  locally-minted session cookie, not a real Google sign-in. Untouched by
  this diff, so the gap is narrow — but it means no branch has exercised
  the real sign-in path since 1.9.4.
- **One event page, one shape.** Only `berlin_marathon` (five races) was
  rendered. **No single-race event and no TBC event was checked** — the
  TBC path takes a different template branch (`locked-panel`, no race
  table) and `Race` is on its hot path too. Low risk, since the diff
  changes no rendering, but it is the untested shape.
- **No deploy.** `deploy: batched`, so the mapping has not run against
  production traffic. It ships with the next batch.
- **The other 53 columns.** That is W-014, and until it runs, "the model
  matches the view" is a claim about exactly one column.
