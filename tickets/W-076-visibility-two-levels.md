# W-076 — Visibility has three levels; Crews v1 needs two

`priority: 2` · `effort: S` · `area: services` · `deploy: immediate`
`source: docs/IDEAS.md 2026-10-31 (Crews v1, Paulo's decision 1) + 2026-10-31 (sharpen the visibility wording)`

**Crews arc, step 0. Lands before the hub (W-077).** See `docs/PLAN.md`.

## What is wrong

Crews v1 rule 2 says every crew a runner belongs to sees their attendance.
Today `private` hides a runner from crew-mates too, so the hub would either
break that promise or break rule 2. Paulo settled it: `private` goes,
leaving `public` and `crews_only`. The settings and profile wording also
describe the levels with two different nouns, and Paulo wants one plain
sentence per level, about **your calendar**.

## Evidence

Paulo, IDEAS 2026-10-31 (Crews v1, decision 1): *"Very good point. collapse to two level only."*

Paulo, IDEAS 2026-10-31 (visibility wording): *"open - your calendar is visible to other indie runners"*, *"crews only - your calendar is visible to your crew"*.

Live data quoted there (analyst, 2026-10-31): **every `private` user is in a crew**; nobody is `crews_only`.

`migrations/009_users_visibility.sql`, the CHECK is inline and unnamed:

```
ALTER TABLE web.users
    ADD COLUMN visibility VARCHAR(16) NOT NULL DEFAULT 'public'
    CHECK (visibility IN ('public', 'crews_only', 'private'));
```

`app/services/settings_service.py:11`:

```
_SELECTABLE_LEVELS = frozenset({"public", "crews_only", "private"})
```

`settings.html` says "your name and past races"; `profile.html:71-75` says "your profile and race calendar".

## Acceptance

1. `migrations/014_visibility_two_levels.sql`, one transaction: `UPDATE web.users SET visibility = 'crews_only' WHERE visibility = 'private'`, then the CHECK replaced by `('public', 'crews_only')`. The constraint's real name comes from `pg_constraint` (read-only), quoted in the ticket's close-out. **Written, not run.** Paulo runs it.
2. `_SELECTABLE_LEVELS` loses `private`; a POST of `visibility=private` is refused the way any unknown level is today.
3. Settings shows two radios: **All indie runners** (stored value stays `public`) and **Crews only**. Each has one sentence about your calendar, in Paulo's words, and the first says *signed-in*: "your calendar is visible to any signed-in indie runner". Each keeps a short clause saying others still see counts (Paulo, 2026-10-31). The profile banner (`profile.html:70-75`) says the same thing in the same words, and its `private` branch is gone.
4. `privacy.html` checked for any statement about who sees what; at triage, a grep for `visib|crew|only you` found only the deletion paragraph (114-117). Quote what you found.
5. Verified signed in: both radios save and re-render checked; the profile banner shows the right sentence for each; preview mode unchanged. Anon unchanged.
6. **Deploy order, in the close-out:** deploy the code first, then run 014. Before 014 runs, the `private` rows are still hidden by `_is_identity_visible`'s fallback (`return False`), which is today's behaviour. Running 014 first would make the old revision's Private radio a 500. In the gap, a `private` user's Settings shows neither radio checked. Say so, and say that saving either one fixes it.

**The label (PM, 2026-10-31).** Paulo's worry: "Public" reads as if anyone could see calendars from the index, when a viewer must be signed in. "Open" carries the same risk. "All indie runners" names the audience, and the sentence names the gate. The word "public" survives only as the stored value.

**The `private` users (triage 2026-10-31, read-only query):** Paulo's three test accounts were the only private rows, all in crews. Nobody to tell; 014 moves them to `crews_only`.

## Out of scope

- The hub and every other crews screen (W-077 onward). That includes Settings' crews paragraph, which W-078 deletes.
- `profile_hidden.html`'s "keeps their profile private". Still true for a stranger looking at a `crews_only` profile.
- Renaming the stored value `public`. A label change needs no migration.
- W-066's hidden-attendee lines: the counts logic doesn't change.

## Close-out (developer, 2026-10-31, 1.9.50)

**Constraint, from `pg_constraint` (read-only, via the proxy):**
`conname = users_visibility_check`,
`CHECK (((visibility)::text = ANY ((ARRAY['public'::character varying, 'crews_only'::character varying, 'private'::character varying])::text[])))`.

**`privacy.html`, grep `visib|crew|only you|signed`:** line 38 "A single signed session cookie is set after login to keep you signed", lines 114–117 (account deletion: "crew memberships from the live database immediately … A crew you are the only member of is deleted; a crew you run passes to its longest-standing"). No statement about who sees whose calendar; unchanged.

**Deploy order:** 1. deploy the code (1.9.50). 2. Paulo runs `migrations/014_visibility_two_levels.sql`. Running 014 first would make the old revision's Private radio a 500 (`DataError` on the new CHECK). In the gap, the `private` rows stay hidden from everyone but themselves (`_is_identity_visible` / `_can_view` fall through to `return False`, today's behaviour); their Settings shows neither radio checked and their own profile banner reads **Crews only** (the `else` arm); saving either radio fixes the row. Nobody to tell: Paulo's three test accounts were the only private rows.

**014 run (2026-10-31, on Paulo's word, after `00067-t94` was serving):** `psql -v ON_ERROR_STOP=1 -f` via the proxy: `BEGIN / UPDATE 3 / ALTER TABLE / ALTER TABLE / COMMIT`. After: no `private` rows remain; `users_visibility_check` is `IN ('public','crews_only')`. The gap state (Settings as a still-`private` user) was not observed; the gap lasted minutes.

**Not done on purpose:** `_is_identity_visible` / `_can_view` keep the fallback; the Crews paragraph on Settings (W-078); `profile_hidden.html`.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-073** — 2026-10-31. One ticket:
code plus a migration file that is written, not run; the run is Paulo's
step and the order (code, then 014) is stated in the close-out, the
changelog and the file header, with the reason (the old revision's Private
radio would 500 against the new CHECK). The `return False` fallbacks are
kept on purpose and are what hides the `private` rows during the gap.
The constraint name matches what 009 generates for an inline column CHECK
(`users_visibility_check`), and CI applies `migrations/*.sql` on a fresh
database with `psql -f`, so 014's DDL runs on every push after merge; the
explicit `BEGIN`/`COMMIT` is right for that. Changelog gives the wrong
belief, the cost, the new belief and the evidence. `privacy.html` grep
quoted. Docs 52/100. `deploy: immediate` (crews arc).

W-073 (docs only, already open) now also carries ARCHITECTURE:190, which
still says the profile banner uses the settings radios' language
"`Public` / `Crews only` / `Private`" and that `public` reads "every
signed-in runner"; the branch changed both labels and left this sentence.

**Not verified:** the gap state itself. Verification used user 1
(`public` throughout); nobody rendered `/settings` or `/profile/<id>` as a
still-`private` user under the new code, so "neither radio checked" and
the banner's `else` arm reading Crews only are read from the template, not
seen. Settling it: Paulo opens Settings as one of his test accounts after the deploy
and before 014. Also not run anywhere with rows: the `UPDATE` in 014 (CI's
table is empty). The `?preview=1` check was done against targets that are
`public` and `crews_only`, which is the whole post-014 set. Not checked:
the branch conflicts with `fix/past-attendance-lock` (W-072, approved) on
`docs/ARCHITECTURE.md`, `docs/CHANGELOG.md` and `docs/TODO.md`; whichever
merges second rebases first. Both changelogs keep their version numbers
(1.9.49 W-072, 1.9.50 W-076).
