# W-011 — the services section restates two counts W-002 corrected, and one it did not

`priority: 4` · `effort: S` · `area: docs` · `deploy: batched`
`source: W-002 review 2026-08-28 (PM), extending docs/DEV_NOTES.md 2026-08-28`

## What is wrong

W-002 re-measured the **core read model** section and dated every count in it.
Its out-of-scope list named "re-measuring the rest of `ARCHITECTURE.md`", and
that boundary was correct. The consequence, which W-002's own changelog states
plainly, is that **the file now disagrees with itself**: the same coverage
claims appear in the services section carrying the old numbers.

The defect is not two wrong figures. It is that the dated-number convention
W-002 introduced is currently a **property of one section rather than of the
document**, and a reader has no way to tell which section they are in. An
undated count in the services section reads exactly like a dated one in the
core read model section did before W-002 — which is the belief W-002 exists to
correct.

## Evidence

`docs/ARCHITECTURE.md:211` — flagged by the developer in `docs/DEV_NOTES.md`:

```
Coverage is sparse — roughly 70 of 236 events carry any format
```

`docs/ARCHITECTURE.md:209` — **not flagged, found in the W-002 review**, the
same defect one paragraph earlier:

```
Cutoff coverage is thin (57 of 234 events), so that filter cuts harder than
its hour range suggests.
```

This ticket supersedes the DEV_NOTES entry, which caught 211 but not 209.

**Both replacements are already measured — no DB session is needed.** Taken
2026-08-28 against `core.v_denormalized_event_data_upcoming`, and independently
re-run in the W-002 review:

```
race_format   non-NULL on  90 of 356 events   (was "roughly 70 of 236")
cutoff_time   non-NULL on 149 of 356 events   (was "57 of 234")
total                     1724 rows / 356 events
```

**The denominators had already drifted apart from each other before either
ticket.** 211 says **236** events, 209 says **234**, and the core read model
section said **233** — three counts of the same corpus at the same moment,
disagreeing. That is the argument for applying the convention file-wide rather
than re-measuring section by section, and it is the reason this is one ticket
covering both lines rather than a correction to the line the note named.

**`cutoff_time` is the one to state carefully.** It has moved the most — 57 of
234 events (24%) to 149 of 356 (42%) in under three weeks, unaided. The
sentence it sits in draws a *conclusion* from it ("that filter cuts harder than
its hour range suggests"), and that conclusion is weakening as coverage climbs.
See `docs/DEV_NOTES.md` 2026-08-28 (evening), where the same trend was the
reason two proposed UI mitigations were dropped.

## Acceptance

- Both counts re-stated with current figures and a `measured 2026-08-28` date,
  in the same form W-002 established in the core read model section.
- The `cutoff_time` sentence's **conclusion** is re-read against the new
  number, not just the number swapped. If "cuts harder than its hour range
  suggests" no longer follows at 42%, say what does — this is the half that
  makes it a docs-integrity ticket rather than find-and-replace.
- The document does not contain two different denominators for the same corpus
  after this ticket. Grep for other undated counts in the sections W-002 did
  not touch and either date them or state that none were found.
- `docs/CHANGELOG.md` version bumped. The entry names the belief: not "two more
  numbers were stale" but "a convention that holds in one section of a document
  is not yet a convention".
- The `docs/DEV_NOTES.md` entry is annotated as superseded by this ticket, not
  deleted.

## Out of scope

- **Re-measuring `web.*` counts.** `ARCHITECTURE.md:147` carries "populated in
  0 of 238 rows" for the dead `source` / `attribution` columns. That is a
  `web.*` table this repo owns, a different query and a different risk, and the
  claim it supports (the columns are dead) is not weakened by the denominator
  moving. Left deliberately; mention it in the changelog if it is re-measured
  anyway.
- **Any code change.** `RACE_FORMAT_CHOICES`, the filter asymmetry, and the
  post-grouping decisions described around those lines are correct and are not
  touched. This is prose.
- **Scheduled or automated re-measurement.** Out of scope in W-002 for the same
  reason and still is — the convention is the fix.
- **Re-opening W-002.** Its boundary was right. This is the follow-up that
  boundary implies, not a correction to it.

## Verdict

**VERDICT: APPROVED** — 2026-10-27. Reviewed `git diff master...fix/architecture-undated-counts`
(`15ac142`, `1342d3e`). Every acceptance item is met:

- Both services-section counts now use the spec's 2026-08-28 figures and carry their dates.
  The old cutoff figure is kept, dated, as the trend.
- The cutoff conclusion was re-read, not swapped. "Cuts harder than its hour range suggests"
  now says what it rests on: most events still have no cutoff. It also says when it stops
  holding.
- The dating note now covers counts "of the view, anywhere in this document". I checked that
  claim myself, because every future count inherits it. I grepped the branch's ARCHITECTURE
  for `N of M` and for `N events|rows|races`. Each count of the view is dated (:44, :70-73,
  :89-90, :121, :244, :246), counted at a stated date (:392, now 2026-08-12), or tied to a
  stated past incident (:77, :443). :168 is `web.*`, which the ticket leaves out. I found
  none that the developer missed.
- The changelog (1.9.35) gives the wrong belief, the cost, the new belief and the evidence.
  It does not claim the figures are current.
- The DEV_NOTES entry is annotated, not deleted. The docs diff is 38 lines.

**Not verified:**
- **The figures themselves.** No DB session, by design: the numbers are from 2026-08-28 and
  are two months old. The dates make that visible. Nothing re-measured them.
- **Whether the note is easy to find.** The document-wide note sits in the core read model
  section, so a reader who starts at the services section never sees it. Each count carries
  its own date, which is the actual fix, so this does not block.
- **The `deploy: batched` deploy.** Docs only. Nothing in the image that users see changes.

No ROUTED_CHECKS entry: nothing in production changes.

VERDICT: APPROVED
