# W-068 — A rollback pin can outlive the rollback: deploy.sh never looks at the traffic split

`priority: 4` · `effort: S` · `area: deploy` · `deploy: none`
`source: docs/IDEAS.md 2026-10-27, infra triage (2) item 1 (Paulo's ruling, infra I-009 option B)`

## What is wrong

`deploy.sh` prints a rollback that pins traffic, and warns that the pin
makes the next deploy's revision receive nothing (`scripts/deploy.sh:104-114`):

```
Roll back to $PREVIOUS:
    gcloud run services update-traffic ... --to-revisions=$PREVIOUS=100

That pins traffic to one revision, so the next deploy of this script will
create a revision that receives none.
```

Nothing checks for it. `serving_revision()` reads `status.traffic[0]`
only, so a deploy under a forgotten pin prints a new "now serving" line
and moves nothing. The old code keeps serving.

From infra's entry in `docs/IDEAS.md` (2026-10-27):

> **1. Traffic is the deploy's (infra I-009, option B).** `web/` will
> ignore `traffic` the way it already ignores the image, so the rollback
> that `deploy.sh` prints stays one command and no apply undoes it. Paulo
> wants the gap this leaves (a forgotten pin) closed **here**, as a web
> ticket. `deploy.sh --check` should print the traffic split. A deploy
> should refuse when traffic isn't on the latest revision, unless a flag
> says the pin is intentional. That's the same pattern as the scraper's
> `deploy_state.py`.

## Acceptance

1. `--check` prints every traffic entry (revision, percent, whether it
   follows latest). Quote the output against production, which is read-only.
2. Without the flag, a deploy exits non-zero **before building** when any
   traffic is not on latest, and names the pin and the `--to-latest`
   command. With the flag it proceeds and says the pin stays.
3. `bash -n` passes. Show the refusal by running the read-only part
   against production, or a stubbed `gcloud` printing a pinned split.
   **Do not pin production to test it.**
4. Changelog says W-057's job 2 runs this script, so the guard covers
   both paths. ARCHITECTURE's deploy section names the flag.

## Out of scope

- Infra's side (I-009, ignoring `traffic` in `web/`).
- W-057 and W-008. All three touch `deploy.sh`. Whichever lands second
  rebases; don't fold them.
- Changing the rollback text beyond pointing at the flag.
