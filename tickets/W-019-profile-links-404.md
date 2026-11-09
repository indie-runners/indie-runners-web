# W-019 — A profile links to event pages the app will not serve

`priority: 2` · `effort: S` · `area: templates` · `deploy: immediate`
`source: AUDIT_20261021T0828 F2 (gitignored — evidence quoted below)`

## What is wrong

The profile and the event page answer "does this event exist?" from two
different sources. The profile builds its rows from `core.events` /
`core.event_occurrences` (`profile_service.py` `_load_rows`), which keeps
every occurrence forever. The event page (`app/main.py:330-347`) selects
from the serving view and 404s on zero rows, and the view drops a non-TBC
race at midnight after its date. So **any attendance row whose occurrence
has left the view links to a 404**, by construction rather than by
accident.

The audit framed it as "Been there links 404". The scope is wider. Every
`been_there` row breaks, but so does a `going` or `interested` row for an
event that has left the MV entirely (`berlin_marathon`,
`half_marathon_berlin`, F6, a scraper-side fault). The defect is that the
profile renders a link without knowing whether it resolves. It is not
about the past.

## Evidence

`app/templates/profile.html:12-13`:

```jinja
{% if row.event_slug and row.occurrence_year %}
  <a href="/events/{{ row.event_slug }}/{{ row.occurrence_year }}">...
```

Probes from the audit, using real attendance rows plus one control:

```
events/berlin_marathon/2026        GET 404   (4 users "going", race 2026-09-26)
events/half_marathon_berlin/2026   GET 404
events/o_see_ultra/2026            GET 404   (6 attendance rows, race 2026-10-17)
events/spartathlon/2026            GET 404
events/zugspitz_ultratrail/2026    GET 404   (4 rows; view now carries /2027 instead)
events/great_south_run/2026        GET 404
events/la_cursa_barcelona/2027     GET 200   (tbc — control)
```

> Attendance with a past `race_date`: **31 of 49 rows**. 13 rows across 8
> users point at an event no longer in the view at all.

So most of what a profile shows today is a dead link, and the share grows
as the season ends.

## Acceptance

1. **No link on a profile page returns 404**, for any flag. The unlinked
   row still shows the event name, location, terrain and date as it does
   now.
2. A row whose occurrence **is** served keeps its link. Check one
   upcoming `going` row and the TBC control (`la_cursa_barcelona/2027`).
3. **Name the mechanism and why.** For example: one query for which
   `(event_slug, occurrence_year)` pairs the view serves, passed to the
   template. Say what it costs per profile render. No N+1, so no query
   per row.
4. Verified in the browser: own profile signed-in, someone else's profile
   signed-in, and a profile anon if anon can reach one. Each is a
   different code path in `profile_service`.
5. Changelog entry with the reasoning. The wrong belief is that "an
   attendance row's event has a page".

## Out of scope

- **A page for a past event** (archive, "finished" view, results). That
  is a product decision nobody has asked for, and it is the same
  territory as W-012's visual treatment.
- **Linking a past row to the next edition** (`zugspitz_ultratrail/2027`).
  It is tempting, but it is a different claim ("you went to *this*
  event") and a feature, not a fix.
- **Why Berlin left the MV.** That is the scraper's. Routed with F6.
- `race_tile.html` and `event.html` links. Both are built from view rows,
  so they resolve by construction.

## Review — 2026-10-21, branch `fix/profile-links-404` @ `311fa93`

The fix is right and the right size. A flag computed in the query the
service already runs, a single constructor, and a template change of one
condition. The EXISTS predicate matches `event_detail`'s (`event_slug`,
`occurrence_year` as text). NULL slugs fall to "no link", which is the
safe direction. The changelog names the wrong belief, the cost (14 of 24
links 404), the mechanism and its measured cost (0.67 ms, index probe
per row). Verification covers own profile, someone else's, a private
target, anon, and the TBC control. Docs: 66 lines, within budget.

**R1 — blocks: the changelog claims "the two cannot drift again", and
the diff makes them two copies.** "Has a page" is now decided twice: by
the ORM query in `event_detail` (`main.py`) and by the raw-SQL `EXISTS`
in `_load_rows`. Nothing ties them together. The next change to
`event_detail`'s predicate, for example a status filter or W-012
reshaping what the page serves, leaves the profile linking on the old
rule. This is the same stale-guess failure this ticket fixes, and the
changelog tells that future developer it cannot happen. **Unblock:**
reword the sentence to name the coupling, and put a one-line comment at
`event_detail`'s query pointing at `ProfileService._load_rows`. Two lines
of prose; no code change needed.

**Noted, not blocking:**
- `1.9.9` skips `1.9.8`, which is held by the blocked W-004 branch. If
  W-004 merges later, its entry must land below this one with its own
  date. That is fine, and recorded here so nobody renumbers.
- Board `status` is still `wip`. That column is the developer's; set it
  to `review` with the R1 fix.
- The DEV_NOTES drive-by (profile location and terrain never render;
  `core.events` has both NULL on all 491 rows) is real and not this
  ticket's. It goes to the next triage.
- `deploy: immediate`: after merge, deploy. Then the PM opens a
  ROUTED_CHECKS entry: under the new revision, zero profile-link 404s in
  the request log.

**Not verified by the PM:** I did not run the branch. The 14/24 and 10/10
figures and the EXPLAIN are the developer's, read from the changelog. The
OAuth round trip was not exercised (minted cookies), which matches house
practice for a change with no auth surface.

**VERDICT: BLOCKED — R1** — 2026-10-21.

## Re-review — 2026-10-21, `5ee7989`

R1 resolved as asked. The changelog now says "decided twice … nothing
enforces that they agree", and `event_detail` carries a one-line comment
pointing at `ProfileService._load_rows`. No logic changed. Status moved
to `review`. The DEV_NOTES drive-by is filed as **W-027**.

**Next:** the developer merges, then deploys (`deploy: immediate`). The
PM opens a ROUTED_CHECKS entry once the revision name is known (W-008:
the revision does not carry the SHA).

**Not verified by the PM:** as before. The branch was not run, and the
figures are the developer's.

**VERDICT: APPROVED WITH FOLLOW-UPS — W-027** — 2026-10-21.
