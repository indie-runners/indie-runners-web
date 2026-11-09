# W-056 — IMAGING.md lists two tiles-bucket grants that don't exist

`priority: 5` · `effort: S` · `area: docs` · `deploy: batched`
`source: docs/IDEAS.md, infra triage 2026-10-26 (from infra I-007's DEV_NOTES)`

## What is wrong

`docs/IMAGING.md` says the tiles bucket grants Storage Object Admin to
Paulo and to the web service account. The live policy grants neither. A
reader who trusts the doc could "restore" a grant by hand, and grants
belong to `indie-runners-infra/web/`.

## Evidence

`docs/IMAGING.md:476-479`:

The doc lists Storage Object Admin for Paulo's account (local publish)
and for the `indie-runners-web` service account (a future service-side
publish). Neither grant exists.

Infra's PM read the bucket policy on 2026-10-26: the live policy grants
only public read (allUsers viewer).

> Local publish runs under the operator's own account. Since infra
> I-007 (applied 2026-10-26T21:43Z), the web SA holds no storage role at
> all. `indie-runners-infra/web/tiles.tf` declares only the `allUsers`
> viewer.

## Acceptance

1. The Principals list matches the live policy. Re-read it with the same
   command when you make the change, and quote it in the changelog.
2. It says local publish works through project Owner. It also says a
   service-side publish would be a grant in `indie-runners-infra/web/`,
   never a hand grant.
3. A changelog entry.

## Out of scope

- **Changing any grant.** Infra owns them. Whether Owner is the right
  identity for publishing is infra's question too, not this ticket's.
