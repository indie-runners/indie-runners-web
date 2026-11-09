# W-031 — Every POST but one trusts SameSite alone, which a sibling subdomain passes

`priority: 4` · `effort: S` · `area: services` · `deploy: batched`
`source: docs/DEV_NOTES.md 2026-10-23 (while on W-022), filed at the W-022 review`

## What is wrong

The app has no CSRF token. The session cookie is `samesite=lax`, which
blocks cross-*site* POSTs but not same-site ones, and any
`*.indierunners.co` host is same-site. W-022 added an `Origin` check to
`POST /settings/delete-account` only. The developer's note:

> The other POSTs (attendance, settings, crews, join) and the GET
> `/auth/logout` rely on SameSite=lax alone, which a same-site page
> passes, for example a hijacked `beta.` CNAME (W-018). None of them is
> irreversible, so it's for the PM to weigh.

Weighed: none is irreversible, and the exposure exists only while a
sibling host can serve someone else's content. W-018 (decommission
`beta.`) shrinks it. So p4, not p2.

## Acceptance

1. Every state-changing route refuses an `Origin` whose host differs
   from `Host`. Name the rule for a missing `Origin` and why.
2. Logout either becomes a POST or is named as accepted (a forced
   logout is a nuisance, not a loss).
3. Each POST still works same-origin, signed in, in the browser.

## Out of scope

- A CSRF token scheme. Say if the Origin check turns out insufficient.
- W-018's DNS work.

## Verdict

**VERDICT: BLOCKED — R1** — 2026-11-01, reviewing
`fix/post-routes-origin-check` at `1ee0ef3`. The shape is right: one
middleware keyed on the method covers every POST and DELETE in
`main.py`, and W-081/W-082's routes before they exist. The PM listed
the routes: attendance POST and DELETE, settings, delete-account,
crews/new, invite/rotate, join. Nothing else takes a non-GET method.
The changelog names W-022's wrong belief, its cost and the new rule,
and it names the missing-`Origin` gap. Logout is accepted per
acceptance 2. `dev.sh` was proved to serve this worktree
(`/proc/<pid>/cwd`). Docs: 39 added lines.

**R1.** The docstring and `docs/ARCHITECTURE.md` say a browser attaches
`Origin` to every POST, so `Origin: null` cannot come from our own
pages. That holds only while no page carries a document-level
`no-referrer` policy. Under one, the Fetch standard sends `Origin: null`
on a form submit. `fetch()` keeps the real origin. Today the only
`referrerpolicy` attributes sit on `<img>` tags, which do not count.
The site already sets `no-referrer` per image. So a later privacy pass
adding `<meta name="referrer" content="no-referrer">` or the header is
plausible. Every form (settings, delete-account, crews) would then
answer 403 "cross-origin request refused", and nobody would look for
the cause in a meta tag. Unblocked when the docstring and ARCHITECTURE
state that condition. The changelog's curl verification stands in for
a browser only under the same condition, and it should say so.

Routed check 42 is written now, gated on the merge. R1 is docs-only, so
the prediction does not change.

**Not verified:** a real browser form submit. Curl sent the same
`Origin` header a browser would, given no document referrer policy.
Production `Host` equal to the browser's `Origin` host is not verified
either. The TODO's evidence, W-022's check running "without a 403 on
real deletions", counts deletions nobody has counted. Better evidence
is that `CanonicalDomainMiddleware` redirects `www.` and `beta.` in
production, so `Host` carries the public name there. Routed check 42
settles it. The `confirm=delete` path was not run, by design.

**VERDICT: APPROVED** — 2026-11-01, re-reviewing at `4071fab`. R1
resolved. The docstring, ARCHITECTURE and the changelog's "Not
verified" line each state the condition: the missing/null-`Origin`
claim holds only without a document-level `no-referrer` policy, and
per-`<img>` `referrerpolicy` does not count. The only code change is
the docstring. The TODO also stops claiming the production `Host`
question is settled and points to routed check 42. Docs: 41 added
lines. Routed check 42 stands as written. Ticket is `deploy: batched`.

**Not verified:** unchanged from the first review. Nobody submitted a
form from a real browser, and nobody confirmed production `Host` equals
`Origin`. Routed check 42 settles the second.
