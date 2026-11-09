# W-017 — The canonical redirect is still the temporary one, six weeks on

`priority: 3` · `effort: S` · `area: routing` · `deploy: batched`
`source: exports/ideas/apex_domain_followups.md (2026-07-27, UNTRACKED —
evidence quoted inline); triaged 2026-09-08`

## What is wrong

`CanonicalDomainMiddleware` 302-redirects `beta.` and `www.` to the apex
host. `app/main.py:63-70`, verified in the working tree on `master`:

```python
class CanonicalDomainMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.hostname in _REDIRECTED_HOSTS:
            return RedirectResponse(
                url=str(request.url.replace(hostname=_CANONICAL_HOST)),
                status_code=302,
            )
```

**302 was correct when it shipped and is a deliberate temporary state**,
not an oversight. The rollout note explains why, and the reasoning is
sound enough to quote rather than paraphrase — the source file is under
`exports/`, which is gitignored, so a path reference would be unreadable
from the worktree where this gets fixed:

> **Why not yet:** 301 is cache-poison for rollback. If we ship 301 and
> apex breaks, reverting the middleware does not help — browsers keep
> following the cached 301 for weeks. 302 keeps the escape hatch open.

**The defect is that the escape hatch was never closed.** The condition
was "~7 days of no apex regression reports". Apex shipped **2026-07-27**;
it is now **2026-09-08** — six weeks, not one. The gate did not fail, it
expired unnoticed, because nothing was tracking it. A temporary state
with no owner becomes permanent by default, and that is what happened.

**Two documents now state the pending action as a settled fact**, which
is how this stops being noticed at all:

- `docs/ARCHITECTURE.md:510` — "302 (not 301) during rollout so rollback
  is not cache-locked in browsers; promote to 301 once stable."
- `docs/CHANGELOG.md:1013` (the 1.7.x apex entry) — the same sentence.

Both read as descriptions of a current, intended configuration. Neither
carries a date or a trigger, so a reader six months from now inherits
"this is how it is" rather than "this is step one of two."

## The "skip" clause, and why it does not apply

The source file offers an out, quoted in full:

> **Skip if:** beta had no external inbound links (no shared beta URLs,
> no beta pages indexed by Google). In that case 301 buys almost nothing
> over 302 — the only real cost of staying on 302 forever is one extra
> redirect hop per bookmarked beta visit.

**That call is taken here: do not skip.** The clause weighed 301's
rollback risk against *speculative* SEO value, and both sides of that
weighing have since moved.

The rollback risk is gone — six weeks of apex serving is the stability
the original gate asked for. And the SEO value is no longer speculative,
because two tickets now on the board ship canonical-host declarations to
crawlers: **W-006** (`robots.txt`) and **W-010** (`sitemap.xml`), whose
acceptance already requires absolute `https://indierunners.co` URLs
"matching the canonical host exactly". Publishing a sitemap that asserts
apex is canonical while the legacy hosts answer with a *temporary*
redirect tells a crawler two different things. The audience W-006 and
W-010 exist to serve is exactly the audience that reads the difference
between 301 and 302.

## Sequencing

**Before W-006.** W-005 set the precedent that the first routing ticket
to land decides the question the rest inherit; this is that question for
the canonical host. Landing it after means W-006 and W-010 are written,
verified and shipped against a host posture that then changes underneath
them.

## Acceptance

1. `app/main.py:68` — `status_code=302` becomes `status_code=301`.
2. `curl -sI https://www.indierunners.co/` returns **301** with
   `Location: https://indierunners.co/`, and the same for a path with a
   query string, confirming path and query are still preserved.
3. `curl -sI https://beta.indierunners.co/` returns 301 likewise.
4. `GET https://indierunners.co/` still returns 200 and renders — the
   apex path is untouched and must be confirmed untouched.
5. **`docs/ARCHITECTURE.md:510` is corrected**, not appended to. The
   sentence must stop saying "promote to 301 once stable" and start
   describing 301 as the current state, with the date it was promoted.
6. **The changelog entry names the wrong belief**: that a temporary
   redirect with no tracked expiry would be revisited. Note that the
   1.7.x entry described a state that has since changed; the new entry
   supersedes it rather than editing history.
7. Verified anon. Signing in is not affected, but confirm sign-in still
   works from the apex host once, because the OAuth callback host and
   the canonical host are the same string.

## Out of scope

- **Removing `beta.` from anything** — the OAuth Client's redirect URIs,
  the Cloud Run domain mapping, the DNS CNAME. That is **W-018**, it is
  operator work rather than a code change, and it depends on this
  ticket: do not dismantle the escape hatch in the same breath as
  committing to a cached redirect.
- **Moving the redirect to a CDN or DNS layer.** Considered and dropped
  in triage — see the `docs/IDEAS.md` note of 2026-09-08.
- **`robots.txt` and `sitemap.xml`.** W-006 and W-010; this ticket only
  makes the host answer they will both assert.
- **Any change to `_REDIRECTED_HOSTS` or `_CANONICAL_HOST`.**

## Review — 2026-10-22 (PM)

Branch `fix/canonical-redirect-301` at `0de0f62`.

**Sound, and exactly as scoped.** One line: `status_code=302` becomes
`301`. `_REDIRECTED_HOSTS` and `_CANONICAL_HOST` are unchanged. The
middleware still runs outermost, so the apex path is untouched. The
changelog names the wrong belief (a temporary redirect with no tracked
expiry gets revisited), says plainly that the cost to people was small
and the cost to crawlers is the point, and supersedes the 1.7.x entry
without editing it. ARCHITECTURE is corrected in place, dated, and now
says what a rollback costs. W-018 stays separate. Docs: 43 lines.
Merges cleanly.

**Paths checked.** `HEAD` was checked as well as `GET` (W-005's
contract). Path and query are preserved. `POST` to a redirected host is
no different under 301 than under 302, since browsers turn both into a
`GET`.

**Not verified:** acceptance 2, 3 and 7 need production. The developer
says so rather than implying it. The PM confirmed the baseline on
2026-10-22: `www.` and `beta.` both answer `302` to
`https://indierunners.co/`. The prediction is `docs/ROUTED_CHECKS.md`
entry 6. **Deploying this is the point of no easy return.** A cached
301 outlives a rollback. That was the ticket's premise, and it is
accepted.

**VERDICT: APPROVED**
