# Plan: Crews v1

> The PM's plan of record. Rewritten 2026-10-31. The previous arc
> (hardening the deploy path and the read model, 2026-08-28) is in git
> history. It was overtaken by the CI/CD plan of 2026-10-25, which lives
> outside this repo, and its order table had been finished for weeks.
>
> **Arc complete 2026-11-04** (triage 2026-11-05): W-098, its last step,
> serves in `00092-vzb`. No next arc is chosen; that is Paulo's, as an
> `IDEAS.md` entry. Until then the board runs in the order below, under
> the batch rule.

## Why this arc

Paulo, 2026-10-31: *"This has the highest prio until it is done, if there
are open tickets that need to be done before, then those go higher in
prio."* The spec is his, agreed that day, and quoted in full in
`docs/IDEAS.md` (§ Crews v1). Its outcome: *a runner who joins a crew can
see, in under a minute, which races the crew is converging on over the
coming months, and can add themselves to the plan from that page.*

**Amended 2026-11-01.** The last clause is dropped with W-079: a member
adds themselves from the event page, as before. And **W-090** (names as
`Paulo M.`) goes ahead of every remaining step, on Paulo's word.

**Half of it is already live.** Tables, create, join by link and the
member-only page shipped in PR3. So the spec's data-model block is
**not** a migration, and build steps 1, 2 (create) and 5 (join) are done.
What is new is the agenda, the toggle, "Next:", leave and remove, and
"My crews" on the profile. Paulo's six decisions on 2026-10-31 settle
where the spec and the live code differ: two visibility levels, roles
kept, TBC rows shown, the confirm step kept, the hidden page kept, and
"My crews" moved to the profile.

## Order

One at a time, in this order. Each step ships on its own.

| # | Ticket | Why here |
|---|---|---|
| 0 | **W-072** (in review) | Already built. W-079's toggle wraps the two methods it changes, so it merges first. |
| 1 | **W-076** two visibility levels | The hub promises that every crew sees your plans, and `private` breaks that promise. The only migration in the arc, and Paulo runs it after the code deploys. |
| 2 | **W-077** hub agenda | The outcome itself. |
| 3 | **W-078** My crews + nav | Spec step 2's other half. Leave (W-081) lands on it. |
| 4 | ~~**W-079** attendance toggle~~ | **Dropped 2026-11-01.** Shipped as 1.9.54, reverted as 1.9.55. Paulo: *"It did not make sense to have these buttons."* |
| 5 | **W-080** members box | Folds in W-042. **Amended 2026-11-02:** the per-member "Next:" line is dropped on Paulo's word; profile links and invite wording remain. |
| 5b | **W-095** hub: no hint, no filter | Added 2026-11-03, Paulo's two asks of 11-02. Deletions only, before W-081 because W-081 edits the same template. **W-094** (a sign-in 500, not crews) goes ahead of it. |
| 6 | **W-081** leave | Shares one hand-over with `delete_account`, or the leftover check 500s. |
| 7 | **W-082** admin removes | Paulo's decision 2, beyond the spec's In list. Reuses W-081. |
| 8 | **W-101** profile empty states | Added 2026-11-04, Paulo's "highest priority, part of the crews arc". A first-time runner's first look at crews. |
| 9 | **W-096** tiles lose the controls | Same entry: raised into the arc. |
| 10 | **W-098** profile in the hub's calendar format | Same entry. After W-101, which boxes the calendar's empty state this keeps. |

**Nothing else on the board has to land first.** W-031 (Origin checks)
does not block: W-081 and W-082 take the delete route's check
themselves, because an only member's leave deletes a crew, and the other
new POST is as recoverable as today's. W-052 (a crew name over 120
characters is a 500) is not reachable from a browser. W-057 and W-060
stay gated on Paulo and block nothing here. After the arc,
W-107, W-108 and W-103 shipped (1.9.68 to 1.9.70), then W-102 and W-018.
Next: **W-111** (pre-commit denylist, before the public flip), then W-112
(lock the Python dependencies, Paulo's "highest prio"), then W-109 (a
malformed profile or event URL answers raw JSON, p2), W-083 (stats wording), W-088
(registration wording), W-099 (search), W-097 (suggest copy). W-100
dropped 2026-11-05, Paulo.

## What this arc excludes

From the spec's Out list: role management UI and member approval, per-crew
settings or visibility, email invites, notifications, the matrix view. So
**the crew digest** (IDEAS 2026-10-30) waits for v1. When it comes back it
is an email provider, a scheduler in infra and a privacy-page change, not
a template. Also excluded: a second edition in one year (EcoTrail Paris),
which is `core.*` and raw on the scraper side.

## Standing rules this arc keeps

- **Every crews ticket is `deploy: immediate`**: Paulo (2026-10-31) wants
  each step on production as it merges, and W-076's migration can't run
  before its code is serving. The batch rule (2026-10-21: a batch ships
  with the next `immediate` ticket, or 14 days after a `done` fix) still
  governs everything else, and the PM checks it every triage.
- **A migration is written by the developer and run by Paulo.** W-076's
  `014` is the arc's only one. If any other crews ticket starts to need
  DDL, it was mis-scoped.
- **One connection budget, two repos.** One DB-touching session at a time.
- **No test suite** (W-003). Each spec carries its own Verify, signed in
  and anon. The hub is signed-in only, so the anon check is the redirect.
- **Close-out:** changelog with the wrong belief, its cost, the new
  belief and the evidence; ARCHITECTURE for any contract change (§ Crews
  and § Visibility both change in this arc); FILE_TREE for new files.
