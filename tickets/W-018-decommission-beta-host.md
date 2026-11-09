# W-018 — Decommission the beta host: OAuth URI, domain mapping, DNS

`priority: 2` · `effort: S` · `area: deploy` · `deploy: batched`
`source: exports/ideas/apex_domain_followups.md items 2-4 (2026-07-27,
UNTRACKED — evidence quoted inline); triaged 2026-09-08`

**NEXT (Paulo, 2026-11-09).** Moved from p4 to p2, ahead of W-109.

## This is operator work, not a developer branch

**Nothing in this ticket is a code change in this repo.** Steps 1 and 3
are actions in the Google Cloud Console and at the DNS registrar. Step 2
is a Terraform plan in `indie-runners-infra` (amended 2026-10-26). There is no diff here,
no branch, and the `branch` column on the board will stay empty — which
is stated here so that an empty branch on a `done` row does not later
read as a lost record. **Paulo executes; the close-out is written into
this file.**

It is a single ticket rather than three because the steps are strictly
sequential and share one gate — beta traffic reaching zero. Split, they
would be three rows waiting on the same observation.

## What is wrong

`beta.indierunners.co` was the pre-launch host. Since 2026-07-27 it has
been redirected to the apex and serves nothing of its own, but three
pieces of it are still live: a registered OAuth redirect URI, a Cloud
Run domain mapping with a managed TLS certificate, and a DNS CNAME.

The reasoning for removing them, quoted from the rollout note (the file
is under `exports/`, which is gitignored — a path reference would be
unreadable from a worktree):

> **Why:** each redirect URI registered on the OAuth Client is an
> independent surface an attacker could target (e.g. if the beta CNAME
> were ever released and a malicious party pointed it at their own host).
> Removing beta once it is dead traffic is minimum-surface hygiene.

That is the whole case, and it is a real one: **a dangling CNAME plus a
still-registered OAuth callback is a takeover shape**, not merely
untidiness. It is `p4` and not higher because it requires an attacker to
first acquire the released hostname, and nothing is currently released.

## Depends on W-017

**Do not run this until the 301 has been live and quiet.** W-017
promotes the redirect to a permanently cached one; this ticket removes
the ability to serve beta at all. Doing them together removes the escape
hatch in the same change that commits to the cache. Order: W-017 ships,
stays quiet, then this.

## The trap, preserved because it is not obvious

Step 1 must not be run early, and the reason is subtle enough that the
source note is quoted rather than summarised:

> **Why not yet:** any user who bookmarked the beta callback URL directly
> would break. The 302 middleware only catches page hits, not the OAuth
> callback path itself (Google only redirects to URIs registered on the
> Client, so if beta stayed registered but the app redirected `beta.`
> elsewhere, the callback would land on apex via redirect and lose the
> `code` query param). Keep beta registered until traffic is truly gone.

**`CanonicalDomainMiddleware` cannot protect this path.** The redirect
drops the `code` parameter, so an in-flight sign-in does not fail
loudly — it lands on the apex homepage signed out, which reads to the
user as "sign-in is broken". Band 1 on `docs/roles/pm.md`'s scale. The
gate is therefore a log check, not a guess.

## Steps, in order, each gated

**Each gate is a log query whose output is quoted in the close-out.** A
step taken without its gate observed is the failure mode this ticket
exists to prevent.

1. **Remove beta from the OAuth Client's Authorized Redirect URIs.**
   Gate: no requests to `beta.indierunners.co/auth/google/callback` in
   the Cloud Run logs for several days. Console → APIs & Services →
   Credentials → OAuth 2.0 Client IDs → the web client → remove the beta
   callback line → save. **Leave apex and `www` registered.**

2. **Delete the beta Cloud Run domain mapping, through Terraform.** Gate:
   step 1 done, plus a few more days of no beta requests at all.
   *Amended 2026-10-26 (infra I-006, applied):* the mapping is now
   `google_cloud_run_domain_mapping.beta` in
   `indie-runners-infra/web/domains.tf`, deliberately without
   `prevent_destroy` ("W-018 (web repo) removes beta by deleting this
   block, plan, apply"). Delete that block and its `import` block there,
   quote the plan (one destroy, nothing else), apply on Paulo's word. A
   Console or `gcloud ... domain-mappings delete` removal now shows up
   as drift in infra, so don't use it.

3. **Drop the beta CNAME at the registrar.** Gate: step 2 done. Delete
   the `CNAME beta ghs.googlehosted.com` record. **This is the step that
   releases the hostname**, so it comes last: while the mapping exists
   the name is claimed, and dropping DNS first is what creates the
   dangling-CNAME window the ticket is closing.

## Acceptance

1. All three steps done in order, each with its gating observation
   **quoted in the close-out**, not asserted.
2. **Sign-in still works from the apex host**, checked after step 1.
   This is the one step that can break sign-in, so the check belongs
   immediately after it and not at the end.
3. `www.indierunners.co` still redirects to apex and its OAuth callback
   URI is **still registered** — `www` is not being decommissioned here.
4. `docs/ARCHITECTURE.md:510` updated: it currently says three domains
   are mapped. After this, two are.
5. Changelog entry naming what was removed and the surface it closed.

## Out of scope

- **`www.indierunners.co`.** It is a live alias with a live redirect and
  is not going anywhere.
- **The 302 → 301 promotion.** W-017.
- **Any code change in this repo.** Step 2's Terraform change is in
  `indie-runners-infra`, with this ticket as its reason. If a change here
  appears necessary, the ticket was
  mis-scoped — stop and re-triage.
- **Monitoring for stray non-apex callback hits.** The source note's
  item 6 proposed this as an ongoing informal habit; it is dropped as a
  ticket, and after step 1 it is moot for beta. See the `docs/IDEAS.md`
  note of 2026-09-08.

## Close-out

**Step 1 — beta OAuth redirect URI removed (Paulo, Console, 2026-11-09 ~15:10 UTC).**

Gate, queried 2026-11-09 before the change. Request logs
(`run.googleapis.com/requests`) start at `2026-10-10T15:15:49Z`; nothing
older is retained, so the gate covers 30 days, not since launch.

- `httpRequest.requestUrl:"beta.indierunners.co/auth/google/callback"`,
  30d → **no rows**. Control: the same filter on the apex host returns
  live sign-ins that day, so it matches when traffic exists.
- Sign-ins started on beta are 301'd to apex before Google is involved,
  so their callback lands on apex, which stays registered.

Sign-in after the change: Paulo signed in on https://indierunners.co in a
browser and landed signed in. Log:

```
2026-11-09T15:15:12Z 307 https://indierunners.co/auth/google
2026-11-09T15:15:24Z 307 https://indierunners.co/auth/google/callback?iss=https://accounts.google.com&c…
```

No beta callback hits after the change.

**Step 2 — beta domain mapping destroyed (infra `cd04912`, applied 2026-11-09 ~15:22 UTC on Paulo's word).**

Gate: as written ("no beta requests at all") it cannot be met. Beta still
drew steady scanner and crawler traffic in the 7 days to 2026-11-09, and
no human requests. **Paulo overrode the gate, 2026-11-09: "human traffic
to beta is null."**

```
# google_cloud_run_domain_mapping.beta will be destroyed
# (because google_cloud_run_domain_mapping.beta is not in configuration)
Plan: 0 to add, 0 to change, 1 to destroy.
```

After apply: re-plan `No changes`; `gcloud beta run domain-mappings list`
shows `indierunners.co` and `www.indierunners.co` only; `curl` apex `200`,
`www` `301 https://indierunners.co/`. Beta was still served a minute
after the apply (a `301` in the app's request log, from my own `curl`):
Google's front end had not yet dropped the mapping.

**Step 3 — beta CNAME deleted at the registrar (Paulo, 2026-11-09 ~15:26 UTC).**

Gate: step 2 applied and re-planned clean (above). Checked at 15:26:59 UTC:

```
beta.indierunners.co @8.8.8.8            status: NXDOMAIN
beta.indierunners.co @1.1.1.1            status: NXDOMAIN
beta.indierunners.co @ns2.wordpress.com. status: NXDOMAIN
www.indierunners.co  @8.8.8.8            CNAME ghs.googlehosted.com.
```

`curl` apex `200`; `www` `301 https://indierunners.co/`. The apex A/AAAA,
`www` CNAME, MX, NS and TXT records were left in place.

**Acceptance:** 1 steps in order, gates quoted (step 2's waived by Paulo,
quoted) · 2 apex sign-in checked after step 1 · 3 `www` still redirects;
its callback was left registered (Paulo removed only beta's line; not
re-read from the Console) · 4 ARCHITECTURE says two mapped · 5 changelog
1.9.73.

## Verdict

**VERDICT: BLOCKED — R1, R2** — 2026-11-09. The work itself is sound and
done in the right order: the callback gate was quoted with a positive
control on apex, sign-in was checked straight after step 1, the plan was
one destroy and re-planned clean, DNS went last and reads NXDOMAIN on
three resolvers. Paulo's waiver of step 2's gate is quoted. Docs 24/100.
What blocks is the text, not the infra.

**R1 — the close-out and changelog carry traffic counts and visitor log
lines** (README § Boundaries, tracked files are public; the same class
cleaned out of `tickets/` in `4a7b3d1` today). Changelog 1.9.73 and
close-out step 2: beta's weekly request count, its breakdown by status,
the scanner paths. Close-out step 1: another user's apex callback with
its timestamp, and the two beta `/auth/google` lines. **Unblock:** say what
was checked and what it showed: beta's callback had no hits in the 30
days of logs; a live apex callback matched the same filter (the control);
beta still drew steady scanner and crawler traffic and no human requests.
Paulo's own 15:15 sign-in lines may stay. The detail goes in an audit
report if it is needed at all.

**R2 — the changelog's wrong belief is not the one this ticket
falsified.** Nobody believed beta "had to stay fully wired"; the ticket
existed to unwire it. The belief that failed was the PM's gate: that
beta traffic would reach zero once humans left. Scanners and crawlers
never stop, so "no beta requests at all" could not be met and was
waived. **Unblock:** the entry names that belief, its cost (a gate that
held a p4 open for weeks and then had to be overridden by hand), the new
belief (gate on the callback path and on human traffic, not on all
requests) and the evidence (the 30-day callback query). One paragraph,
replacing the current first bullet.

**A correction to this spec's own reasoning, for whoever inherits it.**
Step 3 says dropping DNS first "creates the dangling-CNAME window". It is
backwards: a deleted CNAME cannot dangle. The dangling window is the gap
*after* step 2, a CNAME to `ghs.googlehosted.com` with no mapping, which
here lasted about four minutes, and a new mapping needs verified
ownership of the domain anyway. The order was still right for a
different reason: step 2 is the infra plan, and the mapping had to go
through Terraform rather than become drift. Nothing to redo.

**Not verified:** that `www`'s callback URI is still registered (Paulo
removed only beta's line; nobody re-read the Console afterwards). Settles
it: open the OAuth client and read the list. Also not seen: Google's
front end dropping beta. At 15:22:43Z beta was still served, and step 3
went ahead without a recheck. Routed check 57 settles that from the
logs.

### Re-review — 2026-11-09, `09dc28e`

**R1 resolved.** The counts, scanner paths and other users' log lines are
gone from the close-out and from 1.9.73; each now says what was checked
and what it showed. A grep of the ticket and `docs/` for them is empty
(my own R1 paragraph above had quoted them; reworded in this commit).
Paulo's own 15:15 sign-in lines stay, as allowed.

**R2 resolved.** 1.9.73 names the failed belief (beta traffic would
reach zero), the new one (gate on the callback path and human traffic)
and the evidence (the 30-day callback query with its apex control). One
phrase, "held a p4 open for weeks", came from my R2 and is looser than
the record: the ticket sat unattempted at p4, and the gate was first
measured today. The belief, cost and evidence are right; accepted as is.

Step 3's "recheck before step 3" note was rewritten as a plain
observation; that gap stays in **Not verified** above and routed check
57 settles it. Docs 46/100 over the whole ticket. No code change, so
checks 4 and 5 (paths, render) apply only as the apex sign-in and the
`curl` checks recorded in the close-out.

**Not verified:** unchanged from above: `www`'s callback still
registered (re-read the OAuth client), and Google's front end dropping
beta (check 57).

**VERDICT: APPROVED** — 2026-11-09. Operator work, already live; nothing
to merge or deploy. The row's `status` is Paulo's to set to `done`.
