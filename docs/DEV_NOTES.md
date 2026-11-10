# Developer drive-by notes

Append-only inbox. The developer writes here instead of widening a
branch; the PM triages into tickets or drops.

**Tracked in git, and that is the point.** A worktree shares tracked
files with its branch, so a note written from `../irw-W###` arrives in
the diff the PM reviews — which is where a drive-by finding wants to
surface — and survives the worktree being removed. The scraper repo
learned this the hard way: under `exports/` the file existed twice and
was empty in the copy the reviewer read.

Commit it with the branch you are on. The PM triages in place, annotating
rather than deleting: a dropped finding with its reason is worth keeping,
and one that keeps recurring is a signal.

Format:

```markdown
## <date> — while on W-###
<What was noticed. Say whether it is verified or suspected.>
```

---

## 2026-08-28 — while on W-001

**`scripts/dev.sh` leaks the proxy it started when the port race is lost.**
*PM 2026-08-28 — ticketed **W-009**, narrowed. The leak framing does not
survive your own paragraph: you walk it back yourself (`kill -0` guards
the pid that never bound), so the ticket is titled on what is left — the
fixed `sleep 1` treated as proof of a bind. p5: local tooling, no
production path.*
Suspected, not verified — read from the source, not reproduced. `dev.sh`
checks `lsof -ti tcp:5432` and skips starting the proxy if something is
listening. If nothing is, it starts one and traps `EXIT INT TERM` to kill
it. Between the `lsof` check and the bind there is a window where two
sessions both see a free port; the loser's proxy fails to bind but
`PROXY_STARTED` is already `true` and `$!` holds a pid that may have
exited, so `kill -0` guards it — that part is fine. The narrower real
risk is the `sleep 1` being treated as sufficient for the bind: if the
proxy is slow, the app starts against nothing listening and the failure
reads as a DB problem, not a proxy timing one. Would be a one-line poll.

**The deployed revision is not traceable to a commit.** *PM 2026-08-28 —
ticketed **W-008**, p4, spec at `tickets/W-008-label-revision-with-commit.md`.
You drew the W-001 boundary correctly and it is upheld, not reopened. The
ticket splits the verify: the label is only observable on a real deploy,
and `batched` means this does not justify one — so it is confirmed at the
next deploy and recorded in that release's changelog, not claimed here.*
Verified while
building W-001: `gcloud run revisions describe indie-runners-web-00050-6xt`
carries no reference to the git SHA it was built from, because the image
is pushed untagged and nothing labels the revision. W-001 makes the
script *print* the deploying SHA, which helps the operator watching it
run, but does not help anyone asking later "what is actually serving?".
A `--labels=commit=$(git rev-parse --short HEAD)` on the `gcloud run
deploy` would close that, and it is one flag. Out of scope for W-001,
whose brief is the three named guards, and it touches the deploy flags
the ticket said to leave alone. Worth a ticket.

---

## 2026-08-28 — PM triage note, not a drive-by

Written here rather than in a report because **the report it is about is
gitignored and dies with this machine.**

`exports/reports/20260808_new_tickets_from_bugs.md` holds six tickets
(A–F) from the 2026-08-08 batch, written in ticket format "so it can be
dropped straight into the backlog". None ever was. The 2026-08-28 audit
correctly set that file aside as *not a sweep* — true for its own
diffing purpose, and it meant nobody asked what was still live in it.
Triaged now, in full:

- **A, B, C** — `core.*` cutoff data (implausible values, a zero, sparse
  coverage). Scraper repo, never ticketed here. A's `grand_raid_pyrenees`
  rows are the same two the 2026-08-28 sweep re-found as F5 and already
  routed to that repo's `docs/IDEAS.md`. **A is therefore covered; B and
  C are not** — B (`s_25_berlin/kinderlauf`, `cutoff_time = 0.0`) and C
  (coverage: 197 of 967 rows, 57 of 234 events at the time) exist only in
  this gitignored file. **Not routed by me** — routing to the other repo
  writes to a checkout this pass has not read, and C in particular is a
  product question, not a defect. **Carried by the next PM triage pass**,
  which re-measures both and routes them with current numbers. Not
  addressed to the auditor: `docs/roles/auditor.md` lists its inputs as
  production, logs and prior `AUDIT_*` reports, and does not read this
  file — a flag left for a sweep would have been addressed to nobody.
  Until they are routed, B and C live only in a gitignored file and this
  paragraph, which is the whole point of the pattern below.
  *PM 2026-08-28 (evening) — **discharged, both.** Re-measured: B does not
  reproduce (zero non-positive cutoffs in the whole view) and its class is
  already owned by the scraper's `T-025`; C is routed to that repo's
  `docs/IDEAS.md` with current numbers, which moved from 24% to 42% of
  events. C's two web-side mitigations are dropped with a reason. See the
  note at the end of this file.*
- **D** — terrain defaulting to `mixed` on NULL. **Resolved in 1.6.0**;
  `_heal_defaulted_terrain` repairs on read. Verified in the tree today.
  No ticket needed.
- **E** — mobile horizontal overflow. **Resolved in 1.5.2.** No ticket.
- **F** — `mv_id` mapped `Text`, column is `uuid`. **Still live and still
  armed** — confirmed today at `app/models/core.py:17`, with the
  workaround comment at `event_image_service.py:170-177` describing the
  landmine rather than defusing it. **Ticketed as `W-007`, p2**, evidence quoted inline in the spec because its source file is
  gitignored.

**The pattern worth keeping, not the findings.** Six tickets were written
in a form designed to be transferred, into a file that is not tracked,
and five of the six then depended on someone happening to re-read it.
Two were rescued by shipping anyway, one by this pass, and two are still
only here. A finding is not filed until it is on the board.

---

## 2026-08-28 (evening) — PM triage note: B and C, discharged

The previous note left B and C explicitly **carried to the next pass** —
"which re-measures both and routes them with current numbers." This is
that pass, and re-measuring **changed both**, which is the argument for
having carried them rather than routing the 08-08 numbers as written.

Measured against `core.v_denormalized_event_data_upcoming`, 2026-08-28,
1724 rows / 356 events:

```
cutoff_time <= 0                    0 rows
cutoff_time IS NOT NULL           495 rows across 149 events
s_25_berlin / kinderlauf          cutoff_time = NULL
```

**B — `cutoff_time = 0.0` on `s_25_berlin/kinderlauf` — CLOSED, does not
reproduce.** The named row now carries NULL, and **no row in the view has
a non-positive cutoff at all**. B was one row; that row is gone. It is
not routed to the scraper repo, because you do not hand another board a
finding that no longer reproduces — the entry would arrive asking them to
verify an absence.

**The class is not dropped, it is already owned there.** The scraper's
`T-025` ("Price stored without a currency, and cutoff_time has no
instructions", p2, gates T-007) names `zagreb_marathon/kids_races stored
0` as the same defect and its acceptance already reads *"never 0"*. So
the rule that would prevent B recurring is on their board, written from
their own evidence, and a `web-audit` entry restating it from a row that
has since resolved would be noise arriving on a ticket already scoped.

**One consequence for this repo, and it is the half that would otherwise
evaporate.** B's original stated value was *"worth fixing mainly so the
guard in the web layer can eventually be removed"* — that guard is
`app/services/race_service.py:260-262`, which drops `cutoff_time <= 0` at
collection time. **It stays.** Zero rows today is not the same as
impossible: the constraint lives in T-025's acceptance and has not
shipped, so the guard is this repo defending against a source that is
currently clean by luck rather than by rule. Not a ticket — removing it
is a one-line follow-up for whoever closes T-025, and it is recorded here
rather than ticketed because the trigger is on another repo's board.

**C — sparse `cutoff_time` coverage — ROUTED, and the number halved the
severity.** It read **197 of 967 rows / 57 of 234 events (24%)** on
08-08. It now reads **495 of 1724 rows / 149 of 356 events (42%)**. The
corpus grew 53% and cutoff coverage grew faster than it — the share
nearly doubled in under three weeks with nobody working on it. The
premise C was written on ("a user who sets any cutoff range sees at most
24% of the catalogue") is still true in kind and materially weaker in
degree.

Appended to `indie-runners-scraper/docs/IDEAS.md` as one raw entry with
the evidence quoted inline, dated, current numbers plus the trend, and
attributed to the 08-08 report. **Uncommitted on that repo's `main`**,
matching the precedent the auditor set with F4 and F5 — committing to a
checkout this pass does not own is not this role's call. The entry says
plainly that it is a **product question, not a defect**: the filter is
behaving correctly and always was. It also states that **T-025 owns
cutoff *semantics*, not *coverage***, so their PM does not read it as
already covered by a row it sits next to.

**C's web-side half — the two mitigations — DROPPED, with the reason.**
C proposed showing the count of events with cutoff data in the filter
panel, or an "include races with unknown cutoff" checkbox. Neither is
ticketed:

- Both exist to stop a user concluding *"this site has few races"* when
  the truth is *"few races have published cutoffs"*. At 24% that is a
  plausible misreading. At **42% and climbing unaided**, the affordance
  would be explaining a shortfall that is closing on its own, and the
  checkbox in particular contradicts the filter's own semantics — asking
  for races under 12 h is asking for races whose cutoff is *known*, which
  `race_service.py:284-286` already documents as deliberate.
- C's own advice was *"worth measuring bounce behaviour on
  cutoff-filtered sessions first"*, and no such measurement exists. Both
  mitigations are still guesses about a user reaction nobody has observed.

**What would reopen it:** the next audit re-measuring coverage and
finding it flat or falling, or any actual evidence of the misreading.
Re-checking coverage is a cheap standing question and belongs to the
sweep, not to a ticket sitting open on a hunch.

**Both are now discharged.** The 2026-08-08 batch (A–F) is fully
accounted for: A covered by the audit's F5 route, B closed here, C routed
here, D and E shipped, F ticketed as `W-007`. **Nothing in that
gitignored file is still live** — which was the point of the pattern the
previous note ended on.

---

## 2026-08-28 — the stale coverage number is restated outside W-002's scope

*(while on W-002)* *PM 2026-10-22: ticketed **W-011**.* *Superseded by W-011 (1.9.35), which also
fixed the cutoff_time count one paragraph earlier that this note missed.*

`docs/ARCHITECTURE.md:210`, in the **services** section, carries the same
`race_format` coverage claim W-002 just corrected in the core read model
section — and I have deliberately left it stale, because that section is
named out of scope in the ticket:

```
Coverage is sparse — roughly 70 of 236 events carry any format
```

W-002 only re-measures the core read model section, so after my branch
merges **the document disagrees with itself**: `race_format` is on 90 of
356 events in one section and "roughly 70 of 236" in another.

Two things worth knowing before anyone picks this up:

- **No DB session is needed.** Measured 2026-08-28 against
  `core.v_denormalized_event_data_upcoming`: `race_format` is non-NULL on
  **90 of 356** events. That is the replacement value, already taken.
- **The denominator there was already wrong before this ticket.** It says
  **236** events where the core read model section said **233**, and both
  claimed to describe the same corpus at the same time. So this line was
  never a copy of the other one; it is an independently-taken measurement
  that drifted separately. That is mild evidence the fix is a *convention*
  — dated numbers, applied file-wide — rather than a second one-off
  re-measurement, since two undated counts of the same thing already
  managed to disagree.

**Not fixed here on purpose.** The ticket's out-of-scope list names
"re-measuring the rest of `ARCHITECTURE.md`", and a docs ticket that
quietly grows to the whole file is the thing the scope rule exists to
stop. Flagging rather than fixing, per `docs/roles/developer.md`.

---

## 2026-08-28 — `tickets/BACKLOG.csv` is CRLF, and a naive rewrite reflows every line

Found while on W-007, setting my own two columns. *PM 2026-10-22: ticketed **W-015**.*

The file has **CRLF** line endings; every other tracked text file in the
repo is LF. A read-modify-write in Python (`open(p).read()` →
`open(p,'w').write(...)`) silently normalises them, so a **one-cell edit
came back as a 14-line diff** — the whole board rewritten, which is
exactly the shape of "someone crossed the single-writer line" that
`docs/roles/README.md` says a conflict on this file means. It is not; it
is an encoding artefact, and it would have cost the reviewer real time.

Caught here only because the diffstat said 28 changed lines for a
two-field change. Redone with `open(p,'rb')` / `open(p,'wb')` and a byte
literal, which gives the intended 1-line diff.

**So: edit that file byte-preserving, or with a tool that respects its
endings.** `git diff --check` also reports "trailing whitespace" on every
line of it — that is the CR, not real whitespace, and is expected.

**Not fixed here on purpose.** Normalising the file to LF is a one-line
change with a 14-line diff on the board that two roles write to, and it is
nothing to do with W-007. Worth a ticket if anyone wants it; the note is
enough if nobody does.

---

## 2026-08-28 — while on W-007: verifying from a worktree costs two undocumented steps

*PM 2026-10-22: **routed to the chief of staff**, not ticketed. Both fixes
are a paragraph in `docs/roles/developer.md`, which the PM cannot write.*
Verified — both hit on this ticket, both solved, neither written down
anywhere. Process friction, not a code defect. Filing because every
ticket that renders a page pays them, and the developer brief makes
rendering a page mandatory.

**1. `.env` is gitignored, so a fresh worktree cannot import the app at
all.** Not "runs with defaults" — `app/config.py` declares five required
fields and `Settings` forbids extras, so the failure is a pydantic
`ValidationError` on `database_url`/`secret_key`/the three Google keys,
raised from `import app.db`. It fires for `uvicorn` and for any throwaway
script alike. `ln -sf ../indie-runners-web/.env .env` in the worktree
fixes it; the symlink is untracked so it stays out of the diff. **Remove
it before `git add -A`** — I did, but nothing enforces that, and a
committed symlink to a secrets file outside the tree is a bad artefact.

**2. Reaching the signed-in tier needs a cookie you have to mint.** The
brief requires checking both tiers, and the repo documents no way to be
signed in locally. The session is a plain signed Starlette cookie over
`{"user_id": <id>}` — `itsdangerous.TimestampSigner(settings.secret_key)`
over base64 JSON, cookie name `session` (`app/main.py:74-76`, read at
`:106`). Sign one for any existing `web.users` row and pass it with
`curl -b`. That is the whole trick and it took longer to find than to use.

**The limitation matters as much as the technique.** A minted cookie
exercises the *authenticated render*, not the *sign-in*: it skips the
Google round trip entirely. So a branch can honestly report "both tiers
verified" while the OAuth path goes untouched — which is exactly what the
W-007 verdict flags, noting no branch has exercised real sign-in since
1.9.4. Anyone using this should say which of the two they checked.

**Not fixed here on purpose** — out of scope for a mapping ticket, and
the fix is a judgement call I should not make alone: a `scripts/`
helper, a note in the developer brief, or a `.env.example` plus a
documented local user are all defensible and they are not the same
decision. For the PM: this is one candidate ticket, not three.

---

## 2026-08-28 — while on W-005: `dev.sh` can verify the wrong code entirely

*PM: folded into **W-009** at the W-005 review (2026-08-28).*
Verified — hit on this ticket, caught only because the result was loud.
Process friction, not a code defect, and **not** W-009: that one is the
`sleep 1` before the proxy binds. This is a different failure with the
same script.

**What happens.** `scripts/dev.sh` skips starting the proxy if something
already holds 5432, and `uvicorn --port 8000` simply loses the bind if
something already holds 8000. On this machine a uvicorn from the **main
checkout** had been up since Aug 23 on 8000. Running `dev.sh` from the
worktree printed its usual startup lines and exited; my probes then went
to a server running **`master`, not my branch**. The first sweep returned
405 on every page — the exact defect I had just fixed.

**Why the inverse is the real risk.** I caught it because the expected
result and the observed one were 405 vs 200: maximally loud. A ticket
whose change is subtler — a template tweak, a filter boundary, a copy
change — would return plausible output from the wrong code, and the
developer would write "verified in the browser" in the changelog in good
faith about code that never ran. With no test suite that sentence is the
*only* evidence a reviewer has, so this failure mode forges the one
artefact the review depends on.

**How to detect it.** Before trusting a probe, check who owns the port:

```bash
ss -ltnp | grep :8000
ls -l /proc/<pid>/cwd     # must be YOUR worktree, not the main checkout
```

`/proc/<pid>/cwd` is the decisive one — it names the checkout being
served. I ran mine on `--port 8010` instead and left the shared 8000
session alone, since three terminals share this checkout and it was not
mine to kill.

**Not fixed here on purpose.** Out of scope for a routing ticket, and the
fix is a judgement call: `dev.sh` could refuse a held port, pick a free
one, or print the serving checkout's path — and it interacts with W-009,
which already proposes replacing the bind logic. For the PM: worth
folding into W-009 rather than a separate ticket, since both are the same
function of the same script.

---

## 2026-10-21 — while on W-019: the profile never shows location or terrain

*PM 2026-10-21: ticketed **W-027** at the W-019 review.*
Verified, not fixed. `ProfileService._load_rows` reads `e.location` and
`e.event_type` from `core.events`, and **all 491 rows have both NULL**
(`select count(location), count(event_type) from core.events` → 0, 0).
So `profile.html`'s location line and terrain badge never render, linked
row or not. Either the profile reads the wrong source (the view carries
these per race) or `core.events` should carry them, which is the scraper's
call. For the PM to route.

---

## 2026-10-22 — while on W-016: 19 priced rows have no currency

*PM 2026-10-24: routed at the W-016 review; scraper ticketed it T-140.*

Verified, not fixed. In the serving view, 19 rows carry
`registration_price > 0` with `price_currency IS NULL`, across 10 events
(e.g. `kat_100` all four priced races, `lavaredo_ultra_trail` three of
five). W-016 excludes them from the tile range as unknown. The values are
source data, so this is the scraper's (`core.*`), for the PM to route.

---

## 2026-10-22 — while on W-020: first-see picks a tied race by query plan

*PM 2026-10-24: ticketed **W-029** at the W-020 review.*

Verified, not fixed. `list_races` orders rows by `sort_key` only, so when
an event has two races on its earliest date, which one supplies the tile's
location, terrain and price fallback is Postgres's choice, and it changes
with the plan. Measured: under `date_from=2027-01-01`, 24 non-TBC events
showed different first-see fields after W-020 added a predicate, every one
with a tie at its earliest date. A secondary `ORDER BY` key would pin it;
which key is a product call. Same tie-break ARCHITECTURE already records
for location.

---

## 2026-10-23 — while on W-022: only one POST checks Origin

*PM 2026-10-24: ticketed **W-031** at the W-022 review.*

Read, not fixed. W-022 added an `Origin` check to `/settings/delete-account`
only. The other POSTs (attendance, settings, crews, join) and the GET
`/auth/logout` rely on SameSite=lax alone, which a same-site page passes,
for example a hijacked `beta.` CNAME (W-018). None of them is irreversible,
so it's for the PM to weigh.

## 2026-10-23 (while on W-026)

*PM 2026-10-24: 60 cap ticketed **W-037** at the review. Kosovo/Comoros routed to the scraper's IDEAS.md (`0de6fa4`). The Comoros event is `reykjavik_marathon`. Map shortcut: no ticket. Its upgrade trigger is the coverage itself, and three listed countries are already off-map by design (1.9.18).*

- **The index caps at 60 tiles with no "more" signal** (`main.py:247`).
  `/stats` lists Germany at 102, and the click shows "Showing 60 races".
  This predates the map, but the map now advertises a number that the
  click visibly undercuts.
- **`core.*`, for the scraper:** Kosovo's `event_country_code` is `xk`
  (every other row has a lowercased name), so the list and the index
  dropdown both say "Xk". One event geocodes to Comoros (KM), which looks
  like a miss.
- **shortcut:** `static/maps/europe.json` was generated by a throwaway
  script that isn't kept: relative m/z paths made absolute, clamped to
  source box x 440–605, y 205–378 (+5 pad), points under 0.6 units
  dropped, ×4 and rounded. Re-crop from `@svg-maps/world` if the coverage
  moves outside Europe.

- **2026-10-25 (while on W-045):** `timeout 60 bash scripts/dev.sh` did not stop at 60 s.
  *PM 2026-10-26: folded into **W-009** (title widened to teardown): a leftover uvicorn on 8000 is W-009's held-port mode.*
  bash defers its EXIT/TERM trap until the foreground uvicorn exits, and the TERM reached
  bash only, so the proxy and the server outlived the timeout. A SIGINT to uvicorn shut both
  down cleanly. Ctrl-C works because it signals the whole group. This is next to W-009
  (dev.sh's lifecycle); I made no change.

## 2026-10-26 (while on W-033) — for W-032's restore half

*PM 2026-10-26: absorbed. W-032 (1.9.28) quotes it and rule 6 cites it. No ticket.*

The June restore went into a side instance that was deleted within the hour. That is the
pattern a PITR restore follows too (a clone into a new instance). W-032's "re-delete
accounts after a restore" applies to the clone for as long as it exists, and to anything
copied back from it. `gcloud sql operations list --instance indie-runners-db` does not
show restores into other instances. Use Cloud Audit Logs (`restoreBackup`, `clone`).

## 2026-10-26 (while on W-032) — the "Deleted account" log line never reaches Cloud Logging

*PM 2026-10-26: ticketed **W-051** (p4). The acceptance covers the user ids that INFO would start writing, against the privacy page.*

`UserService.delete_account` logs `Deleted account user id=…` at INFO, but nothing in `app/`
calls `basicConfig` or `setLevel`, so the root logger stays at WARNING and every app
`logger.info` is dropped. Evidence: 30 days of `indie-runners-web` logs hold no
`Loaded N dedicated event slugs` (main.py:51, every cold start) and no `Deleted account`, but
uvicorn's own access lines are there. The request log keeps when an account was deleted (a
303 on `POST /settings/delete-account`), not whose. Rule 6's limit follows from this. Ticket
out of scope says logging deletions is its own ticket; I made no change.

## 2026-10-26 (while on W-037) — the index does per-tile work for tiles it then drops

*PM 2026-10-26: dropped. The inserts happen once per new event, and in steady state it is one read of ~386 rows. `/` serves in 0.46s with the pool idle (AUDIT_20261026T0807), so users and the shared budget both see nothing. Reopen if `/` latency becomes an audit finding.*

`index()` assigns tile images (`get_or_create_for_events`, which may insert rows) and loads
attendance for every match, then sorts and keeps 60. On `/` that is 381 events' worth of
work for 60 tiles. The sort needs the attendance counts, so the cut cannot simply move up;
images could be resolved after it. No change made.

## 2026-10-26 (while on W-041) — a crew name over 64 slug characters is a 500

*PM 2026-10-26: folded into **W-049**, now p3 and the next ticket. Confirmed from source: the route catches only `ValueError`.*

`crews_new.html` allows `maxlength="120"` and `display_name` is `VARCHAR(120)`, but `slug`
is `VARCHAR(64)` (`010_crews.sql:24`) and `_slugify` does not truncate. A 65+ character
name should raise a `DataError`, which `create_crew` does not catch. Read from source, not
reproduced. Truncating would also have to stay unique-by-name. No change made.

## 2026-10-26 (while on W-050) — Strava publishes no standalone glyph; acceptance 2 cannot be met

*PM 2026-10-26, at the W-050 review: Paulo chose (a), as the developer's TODO records. W-050's acceptance 2 is amended to match. No new ticket.*

Blocked before the worktree. Nothing built. developers.strava.com/guidelines/ offers exactly
two downloads, `/downloads/1.1-Connect-with-Strava-Buttons.zip` and
`/downloads/1.2-Strava-API-Logos.zip` ("Powered by" / "Compatible with" lockups). Both are
unzipped and neither has a bare mark. The page also says: "Never modify, alter or animate
Strava logos". Its only linking rule is for API data: “View on Strava”. press.strava.com
(where strava.com/press redirects, /about and /contact checked) links no asset kit, and
strava.com/brand is a 404. So the chevron at `mockup_reference.html:21` cannot be checked
against Strava's page. Instagram is fine: Meta's
https://www.meta.com/brand/resources/instagram/instagram-brand/ ships
`Instagram_Glyph_White.svg`. Routes for the PM / Paulo: (a) ship the third-party chevron and
name the gap in the changelog, or (b) Strava stays a text link on the new row until Strava
publishes a mark. Ruled out: cropping the chevron out of a "Powered by" SVG (modification),
and shipping Instagram alone (rewrites acceptance 1).

## 2026-10-26 — while on W-029: tile and profile agree on ties, not on NULLs

*PM 2026-10-27: ticketed **W-055** (p4). Location is fixed on the tile; terrain is counted, not changed.*

Read, not fixed. The tile now breaks ties by `mv_id`, like the profile, but the
profile's location subquery skips `race_location IS NULL` and the tile's
first-see does not. Where the `mv_id`-first tied row has no location, the tile
shows "—" and the profile a town: `otf_presented_by` today (checked after the fix).

## 2026-10-27 — while on W-013: the event page never shows a town, on any event
*PM 2026-10-28: routed to the scraper's IDEAS, body as written, heading and source retagged `web-audit` (0 of 396 populated, re-measured). The leading `·` it shows, plus the lowercase country, ticketed **W-065** (the next ticket). Paulo's "all three agree" ticketed **W-069**, GATED on the scraper.*
*PM 2026-10-28, later: Paulo revised the ruling. The web shows `event_location`, else the first race with a town, else empty, one shared read. That is **W-070**; W-055 and W-069 fold into it and the gate is gone.*

*Corrected 2026-10-27. This first said "when there is no location". It is every event.*

Read, not fixed. The hero reads `event_location` (`main.py:400`), which is NULL on all 391
events in `core.v_denormalized_event_data_upcoming` (measured 2026-10-27). So no event page shows
a town, and the meta row always starts with the `·` meant to follow it:
"· greece · 7 November" (`athens_authentic_marathon/2026`). Race towns exist on 382 events,
96 of which have more than one distinct `race_location`.

**Paulo, 2026-10-27:** the scraper should work out an event location. `race_location` asks
for a race's start, and the event's HQ can be somewhere else. Not a web workaround: don't
fall back to a race town here. **And every place that names an event's location must agree**
(Paulo): today the event hero (`event_location`, always empty), the home tile (first-see row's
`race_location`, `race_service.py:242`) and the profile's race calendar (earliest-dated race's
`race_location`, `profile_service.py:172-177`) are three different reads. The calendar shows
Transgrancanaria in "Artenara", one race's start, not the Maspalomas HQ. When the scraper
populates `event_location`, the web ticket that follows moves all three onto it.
The **name** already agrees: all three read `core.events.event_display_name`. Only the
fallback when it is NULL differs: `event_name` on the hero and tile, the name saved on
`web.attendance` when the user marked it on the calendar (`profile_service.py:168`).

**For the PM to route** to the scraper's `docs/IDEAS.md` (no web ticket):

> ## web-review 2026-10-27 — `event_location` is read by the web event page, so T-039's "consumers are fine" is wrong for it
> source: web-review (indie-runners-web DEV_NOTES 2026-10-27, while on W-013)
>
> T-039 says nothing user-facing is missing because `race_location` carries the town. The
> web event page's hero reads `event_location`, which is NULL on all 391 events of
> `core.v_denormalized_event_data_upcoming` (measured 2026-10-27), so no event page shows a
> town. Paulo's direction settles T-039's open choice for this column: **populate it, don't
> drop it.** It is the event's own location (its HQ), not a race start. The two can differ:
> Berlin Marathon is Berlin for both, but Transgrancanaria is based in Maspalomas, and its
> long race starts in Las Palmas. Deriving it from `race_location` isn't enough: 96 events
> carry more than one distinct race town, some of them spellings of one place
> (`athens_authentic_marathon`: `Athens`, `Αθήνα`, NULL). Possibly a question of its own in the
> answers, like `race_location`. The web shows an event's location in three places (event
> page hero, home tile, the profile's race calendar) and they must agree. Today the tile and
> calendar fall back to a race town, so the calendar lists Transgrancanaria in Artenara, one
> race's start. Once `event_location` is populated, the web moves all three onto it.

## 2026-10-27 (while on W-023) — one event's end date stops before its last race
*PM 2026-10-28: routed to the scraper's IDEAS, re-measured (still 1 of 239 dated occurrences, Athens only).*

`athens_authentic_marathon` 2026: `occurrence_end_date` is `2026-11-07`, but a race in the view
is dated `2026-11-08`. 1 of 233 dated occurrences (max `race_date` > `occurrence_end_date`); no
start-date mismatches. The hero prints "7 November" for a two-day event. W-023's calendar link
spans the races instead. `core.*` content, so **for the PM to route** to the scraper's IDEAS.

## 2026-10-27 (while on W-028) — ARCHITECTURE names an action-bar avatar strip that isn't there
*PM 2026-10-27, at the W-028 review: ticketed **W-062** (the claim) and **W-063** (the screen-reader count). Annotated at triage 2026-10-28.*

ARCHITECTURE § Who's coming says "the action bar continues to trim display via the shared
`avatar_strip` macro's `cap` argument". `avatar_strip` is called only from `race_tile.html` and
the anonymous who's-coming row (`event.html:508,516`); the event page has no action-bar strip.
W-028 corrected the same claim in the § above it, not this one (out of scope). Also: the anon
who's-coming row's only label is its Going/Interested heading, so a screen reader hears no count.

## 2026-10-28 (while on W-066) — a wording candidate for W-063, and attendance on a past date
*PM 2026-10-29: the wording candidate was added to W-063 at the W-066 review; nothing further. Attendance on a past date ticketed **W-072** (p3).*

W-066 settled the signed-in hidden line as `1 indie runner is going` / `N indie runners are
going`. W-063 (the anon row's screen-reader count) could use the same sentence as its one
label per row; named here as a candidate only. Separately, seen while verifying: the attend
route accepts a `going`/`interested` on a past occurrence (`mark_attendance` stores whatever
date it finds), while `clear_attendance` refuses to delete once `race_date` has passed — so a
row written by mistake on a past edition cannot be undone from the UI.

## 2026-10-30 (while on W-074) — static_url hashes once per process
*PM 2026-10-31: **dropped.** It only affects local dev, the fix is restarting `dev.sh`, and the `shortcut:` comment names the upgrade. W-077 carries the restart line, since the crews arc is the next CSS work. Ticket it if it costs a developer a verification.*

`shortcut:` in `app/main.py` `static_url`: the content hash is `lru_cache`d for the process
lifetime. Right on Cloud Run, where a new image is a new process. Locally, `uvicorn --reload`
watches `.py` only, so an edit to a static file keeps the old `?v=` until a `.py` file is
touched; the browser then holds the old copy as `immutable`. Bites only a developer iterating
on CSS/JS locally. Upgrade (hash by mtime, or no cache under `settings.debug`) if it does.

## 2026-10-30 (while on W-072) — a worktree also needs the proxy binary
*PM 2026-11-01: **handed to the chief of staff**, `docs/handoffs/2026-11-01-pm-to-cos-worktree-proxy-link.md`. The developer brief and `/dev-ticket` are theirs.*

`cloud-sql-proxy` is gitignored beside `.env`, so `scripts/dev.sh` from a fresh worktree tries to
download it again. `ln -s ../indie-runners-web/cloud-sql-proxy cloud-sql-proxy` fixes it; the
developer brief and `/dev-ticket` name only the `.env` link. One line for the CoS.

## 2026-10-30 (while on W-072) — the profile's past/upcoming split reads the start-date snapshot
*PM 2026-11-01: already **ticketed W-084** (p4) at the W-072 review; annotated now.*

`ProfileService.is_upcoming` reads `web.attendance.race_date`, the `start_date` snapshot. Under
W-072's rule an edition stays markable through its `end_date`, so during a multi-day tail
(Tirana 2026-10-25 → 11-15 today) a row shows as past on the profile while the site still
offers Change/Remove. Pre-existing semantics the ruling now exposes; a board decision, not W-072's.

## 2026-10-31 (while on W-077) — anon on `/crews/{slug}` is a 401, not a sign-in redirect
*PM 2026-11-01: already **ticketed W-085** (p3) at the W-077 review; annotated now. The route fix, not the doc fix.*

W-077's acceptance 7 says *"Anon still redirects to sign-in"* and ARCHITECTURE § Crews says an
unauthenticated visitor *"bounces to Google"*. On master (checked with the branch stashed)
`curl localhost:8000/crews/<crew>` is a bare 401 from `get_required_user`; only
`/settings` has the redirect (main.py:646). Out of scope here; a one-line route fix or a doc
fix, the PM's call.

## 2026-10-31 (while on W-078) — two more "← Settings" back links
*PM 2026-11-01: already **ticketed W-087** (p5) at the W-078 review; annotated now.*

`crews_hidden.html:15` and `crews_invite_invalid.html:15` still read "← Settings". W-078 moved the
hub's and the create form's to `/profile`, where crews now live; these two were left because the
spec names the crew page only. Same one-line change if the board wants them.

## 2026-11-01 — reverting W-079 on Paulo's word
*PM 2026-11-01: **W-079 dropped**, not reopened. Paulo: "It did not make sense to have these buttons." W-089 dropped as moot, check 40 retired. PLAN step 4 struck; W-080 is the arc's next step, after W-090.*

**W-079 (1.9.54) is reverted on `master` and reopened, not re-ticketed.**
Paulo did not like the Going | Interested options on the live hub and
asked for the change removed and deployed. The revert is `1.9.55`.
For the PM: W-089 (a refused hub toggle lands on raw JSON) now describes
a route that no longer exists; PLAN.md's crews arc step 3 is open again
and step 4 (W-080) does not depend on it. What Paulo wants instead of
the two segments is his to say, not mine to guess.

## 2026-11-02 — while on W-092: a code that fails the token exchange is a 500
*PM 2026-11-03: **ticketed W-094** (p2, `deploy: immediate`, next), with AUDIT_20261103T0806 F2: three replays of one code hit this path in production.*
`GET /auth/google/callback?code=bogus` lets `httpx.HTTPStatusError` (Google's
400 on the token endpoint) escape as a 500. Named out of scope by W-092's spec
and absent from the log; noted so the board knows the path is unguarded.

## 2026-11-03 — while on W-094: two sibling 500s on the callback stay
*PM 2026-11-04: **ticketed W-105** (p4). Never seen in production; any callback 5xx still shows in every sweep's status mix.*
`httpx.RequestError` (timeout or no route to Google's token endpoint) still
escapes `exchange_code_for_token` as a 500: W-094 handles Google's refusal,
not Google's absence. `get_userinfo` keeps `raise_for_status()`, as the spec
left it; a 4xx there after a good exchange is the same shape, never seen in
the log. Neither touched.

## 2026-11-03 — at W-048's summary, before taking it: the drift check has a CI home
*PM 2026-11-04: **W-048 amended** per Paulo's call: URL from the environment, one step in the `migrations` job (pin verified: `aad6a87`, scraper 0.80.4). Owner of the by-hand run named in the spec.*
Paulo asked why W-048 is by hand and not CI/CD. The spec's reason ("W-045's CI
cannot reach the database") is true of production and should stay so. But the
`migrations` job in `.github/workflows/ci.yml` already builds a throwaway
Postgres from the scraper's `database/baseline.sql` at a pinned ref and
refreshes the MV, so the view exists in CI with its real column names and
types. The script can run there too: one extra step, and a pin bump to a
scraper release that changed the view fails CI until `core.py` follows.
What it cannot catch is drift between the pin and production, which is the
pin's staleness and exists today; the by-hand production run stays for that.
Unverified: that `information_schema` reports identical type names for the
baseline-built view and the migration-built one (both Postgres 15, so it
should). Paulo's call 2026-11-03: leave W-048 open for the PM to amend
(acceptance: URL from the environment, one CI step), developer moves to the
next ticket. Spec also names no owner for the by-hand run.

## 2026-11-03 — while on W-081: the leave flash reads its crew name from the URL
*PM 2026-11-04: **dropped.** Autoescaped, own profile only, and the `shortcut:` names the upgrade. A crafted link needs the target's id and puts one green sentence on their own page. Ticket it if one shows up in the log.*

`shortcut:` in `profile.html`. `POST /crews/{slug}/leave` 303s to
`/profile/{id}?left=<name>#crews` and the own profile flashes "You've left
<name>". So a crafted link to your own profile shows any text in that green
box, autoescaped, own profile only. Upgrade to a one-shot session value if
it is ever abused; the session cookie is already signed.

## 2026-11-03 — while on W-082: two more raw `display_name` renders for W-093
*PM 2026-11-04: already in **W-093** (amended at the W-082 review, 2026-11-03); annotated now.*

The Remove button's confirm text and `aria-label` in `crews_detail.html`
print `user.display_name` raw, so a nameless member reads "Remove None".
W-093's fallback should cover these two lines along with the ones it names.

## 2026-11-04 — while on W-096: ARCHITECTURE:187's "updates the strip and counts via attendance.js" is W-062's line
*PM 2026-11-04: **W-062 amended** at the W-096 review; annotated now.*

After W-096 `attendance.js` rebuilds only the action bar's status and
buttons; it never touched a strip or count on the event page, because the
bar has none (the comment it carried said so). That sentence falls with
the avatar-strip claim W-062 already names; nothing added here.

## 2026-11-04 — while on W-096: tiles still compute and carry `data-gcal-url`
*PM 2026-11-04: **ticketed W-106** (p5) at the W-096 review; annotated now.*

`race_tile.html:7` calls `gcal_url()` once per tile per signed-in render
and writes `data-gcal-url` on the tile; only `offerCalendar` read it, and
after W-096 nothing on a tile can trigger it. Sixty calls per signed-in
index load for an attribute nobody reads. Out of W-096's scope (the
calendar offer belongs to the event page); one line to drop if the PM
agrees.

## 2026-11-04 — while on W-107: a wrapped row on the narrowest tile, and leftovers
*PM 2026-11-05: leftovers **folded into W-106** (`size`, `.avatar--lg`, and `.hover-avatar`: verified dead, the mockup that uses it loads `styles.css`). The clip with no sign is **left raw**: settled by anyone seeing a cut row on production. Curl cannot see layout, so no check carries it. Paulo 2026-11-05: none seen since 1.9.69.*
`shortcut:` in `main.css` at `.hover-rows` (rewritten by W-108): the rows still
clip with no sign when the fixed blocks leave too little room. W-108 removed the
wrap and tightened 1101 to 1130px until today's tiles fit, nothing more. Spare
room at 1101px, signed out, measured over the month filters: four tiles of 458
at -0.4px (Stuiben Trailrun, Val Daran Pyrenees, Bucovina Ultra Rocks, Gletscher
Trailrun), San Sebastian +0.6px. A longer name, or one more block, cuts the entry
fee again. Upgrade to a visible sign, or row ranking (Paulo's call), when it does.
W-107 removed the last `avatar_strip(..., 'lg')` calls, so the macro's `size`
argument and `.avatar--lg` are now dead. `.hover-avatar` in `main.css` was dead
already. Left alone, out of W-107's scope.

## 2026-11-08 — while on W-102: the back link's filters survive one hop
*PM 2026-11-10 — no ticket. Pre-existing, not a regression, and the upgrade trigger is named. Whether filters should survive the race-table hop is Paulo's call, raised at triage.*
`shortcut:` in `main.py` `event_detail`: the back link reads the filters from
`Referer`, so choosing a race in the event page's table (a full navigation to
`?race=`) makes the event page the referrer and the link falls back to `/`.
Same as before W-102, not a regression. Upgrade if the race table stops being
a full navigation, or if Paulo wants the filters to survive it.

## 2026-11-09 — while on W-018: `beta` in `_REDIRECTED_HOSTS` is now dead
*PM 2026-11-09 — ticketed **W-113** (p5, still a frozen row; refiled when wanted).*
`app/main.py:69` still lists `beta.indierunners.co`. Its mapping is gone, so
the app no longer receives beta requests once Google's edge drops it. Harmless;
removing it is a code change, out of W-018's scope.

## 2026-11-10 — while on W-114: `gh pr edit` fails, so the dev-ticket recipe does too
`gh pr edit 24 --body-file …` exits 1 on GitHub's Projects (classic)
deprecation error (`repository.pullRequest.projectCards`) and leaves the body
unchanged. What worked: `gh api -X PATCH repos/indie-runners/indie-runners-web/pulls/<N> -F body=@<file>`.
`/dev-ticket` § 5 belongs to the chief of staff.
