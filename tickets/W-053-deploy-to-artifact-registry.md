# W-053 — `deploy.sh` pushes to multi-region `gcr.io`; the web's own registry sits empty

`priority: 4` · `effort: S` · `area: deploy` · `deploy: batched`
`source: docs/IDEAS.md, infra triage 2026-10-26 (indie-runners-infra I-002)`

**SUPERSEDED 2026-10-27 (PM): folded into W-057.** W-057 builds in the
runner and drops Cloud Build, so acceptance 1 (a `builds submit` to `web`)
no longer tests anything. Acceptance 2-3 are W-057's now. Don't take this.

## What is wrong

The web image goes to `gcr.io`, a multi-region `us` registry that infra
plans to retire, while the service runs in `europe-west1`. Infra's I-002
created a regional `web` Artifact Registry repo for this image and left
the switch to this repo. Until it moves, infra cannot retire `gcr.io`.

## Evidence

`scripts/deploy.sh:44`:

```
IMAGE="gcr.io/$PROJECT/$SERVICE"
```

I-002, quoted in `docs/IDEAS.md`:

> **Moving the web deploy off `gcr.io`.** This ticket creates the
> registry; switching `deploy.sh` to push there is the web repo's change,
> in its own ticket. Retiring the `us` `gcr.io` repo follows that, not
> this.

`gcloud artifacts repositories describe web --location=europe-west1`,
PM 2026-10-26:

```
Repository Size: 0.000MB
format: DOCKER
labels:
  goog-terraform-provisioned: 'true'
registryUri: europe-west1-docker.pkg.dev/indie-runners-dev-470411/web
```

`docs/ARCHITECTURE.md:530` names the old path:

```
The container image is built via Cloud Build and stored in `gcr.io/indie-runners-dev-470411/indie-runners-web`.
```

### Grants, checked by infra (2026-10-26)

`scripts/deploy.sh:83` runs `gcloud builds submit --tag "$IMAGE"` with no
`--service-account`, so the build runs as the default build service
account and pushes through a broad project role; the web repo has no
grants of its own. Nobody has run the push yet. **Infra I-008 narrows
that account's role.** Acceptance 1 is still the test. If the push fails
on a permission, check I-008: then it is not a W-053 problem, but every
deploy losing its build identity. Infra routes that replacement. Don't
hand-grant either way.

## Acceptance

1. **Push first, without moving traffic.** Run
   `gcloud builds submit --tag europe-west1-docker.pkg.dev/indie-runners-dev-470411/web/indie-runners-web --project indie-runners-dev-470411`
   on its own. It succeeds, and the `web` repo's size goes above 0.
   **If it fails on a permission** (Cloud Build writing to `web`, which
   `gcr.io` never needed a grant for), stop. The grant is an infra change
   in `indie-runners-infra/web/`. Set the row to blocked and say so in
   `DEV_NOTES.md`. Don't grant it by hand.
2. `IMAGE` in `deploy.sh` is that path. Nothing else in the script
   changes.
3. ARCHITECTURE.md:530 names the new path. CHANGELOG entry as usual.
4. The first real deploy after the merge creates a revision whose image
   is under `europe-west1-docker.pkg.dev/…/web/`, and `/` answers 200.
   This acceptance step is the deploy itself, so whoever runs the next
   deploy checks it. If Cloud Run can't pull the image, the deploy fails
   and the old revision keeps serving.

## Out of scope

- **Retiring `gcr.io`.** That's infra's (I-002), and it waits on more
  than this merge. Every revision up to the switch was deployed from a
  `gcr.io` image, and rollback here is by revision
  (ARCHITECTURE.md, Deployment). It is **not established** whether a
  revision can still cold-start after its image is deleted. Infra should
  settle that, or wait until a post-switch revision is the rollback
  target, before it deletes anything.
- Image tags and revision labels: W-008, which touches other lines of
  the same script and is blocked on infra.
- `.github/workflows/ci.yml`: it only runs `docker build .` and pushes
  nothing.
- `CHANGELOG.md:1096` and W-008's text mention `gcr.io`. Both were true
  when written, so leave them.
