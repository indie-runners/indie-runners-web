# W-057 — Gated CD: build in the runner, deploy on approval

`priority: 2` · `effort: M` · `area: infra` · `deploy: immediate`
`source: claude/CICD_TERRAFORM_PLAN.md step 4 (Paulo, 2026-10-25)` —
sequence 8 (web) of that plan. Paulo listed it as depending on infra
sequences 3 (I-002) and 5 (I-006), and both are done. **It is gated on a
third infra change that neither of them made** (correction 1).

`deploy: immediate`, because the first run through the workflow is a
real deploy and is acceptance 3. Paulo set it.

## What is wrong

A deploy is `./scripts/deploy.sh` on Paulo's laptop. It builds through
Cloud Build as the compute SA (project Editor) and moves traffic with no
second pair of eyes. Nothing records what was deployed or from where,
except the terminal it ran in.

## Prerequisites

1. **Paulo: a `production` environment with a required reviewer.** The
   developer checks it before starting and quotes it here:
   `gh api repos/indie-runners/indie-runners-web/environments/production`
   shows a `protection_rules` entry of type `required_reviewers`. At
   triage the environments call returned 404 and the org's plan wasn't
   readable (no `admin:org` scope), so neither is verified. **Required
   reviewers exist only on environments.** If the plan doesn't offer them
   on private repos, the ticket is blocked, not worked around: the gate
   is the point of the ticket.
2. **Infra: a deploy identity for this repo** (correction 1), routed to
   `indie-runners-infra/docs/IDEAS.md` as `web W-057 2026-10-27`.
3. **Paulo: repo variables** taken from the `platform/` and `web/`
   outputs: the WIF provider, the push SA and the deploy SA. Use
   `vars.*`, no `secrets.*` (W-045's rule).

## Amended 2026-10-28 (triage): infra I-015 and I-017

From `docs/IDEAS.md` (infra triage 2026-10-27 and 2026-10-27 (2)):

- **Prerequisite 2 is infra I-015**, still open there. Push SA:
  `artifactregistry.writer` on `web` only, repo-wide principal set.
  Deploy SA: a role on the service (ceiling `run.developer`),
  `serviceAccountUser` on `indie-runners-web@` only,
  `artifactregistry.reader` on `web`, and `workloadIdentityUser` bound
  to `repo:indie-runners/indie-runners-web:environment:production`
  (correction 1's design, adopted). Both emails are `web/` outputs, for
  prerequisite 3. Still GATED until I-015 is applied.
- **Tags on `web` are immutable** (I-017, applied, infra `5f97f38`). A
  push to an existing tag is refused, so `cd.yml` pushes the version tag
  only, never a moving tag such as `latest`. Re-running a tag's job
  fails by design; say so in the changelog.
- **Job 2 deploys by digest.** Paulo: *"Not optional. Fix it, and fix it
  twice."* Job 2 resolves the tag to its digest, passes
  `…/indie-runners-web@sha256:…` to `deploy.sh`, and prints tag and
  digest in the run log for the approver. Acceptance 2 reads "that
  digest" where it says "that image ref".
- **Left to this ticket** (I-015's out of scope): the Cloud Run pull
  from `web` rides on `run.serviceAgent`, unexercised. The first deploy
  is the test. A failure is routed to infra, never hand-granted.
- Don't restrict which branches may push (Paulo).

## Amended 2026-10-29 (triage): I-015 applied; who may request a token

- **Prerequisite 2 is met.** I-015 was applied 2026-10-28T14:47Z (infra
  `6ee816d`, "web/ re-plans No changes"). The ticket no longer waits on
  infra.
- **Prerequisites 1 and 3 are still open.** At triage
  `gh api repos/indie-runners/indie-runners-web/environments/production`
  returned 404, `gh variable list` printed nothing, and the repo is
  `private`. Required reviewers on a private repo depend on the org's
  plan, so the public flip may be what unblocks prerequisite 1.
- **The push SA trusts the whole repo** (infra's I-015 review, IDEAS
  2026-10-28): once public, any workflow run that gets `id-token: write`
  can push a new tag. So: `id-token: write` appears only on `cd.yml`'s
  jobs (grep `.github/workflows/`, quoted). `ci.yml` requests none. No
  `pull_request_target` workflow is added. Narrowing the binding instead
  is an infra `web/` change, out of scope here.

## Four corrections to the paste

1. **Nothing binds the web's principal set.** `platform/ci.tf` creates
   all three principal sets and binds only infra's:

   ```
   member             = local.principal_sets["indie-runners-infra"]
   ```

   I-002 left the rest out of scope on purpose: "Deploy permissions for
   the app repos' principal sets. This ticket creates the principal sets;
   what each app's CI may do is that app's module's ticket." So
   `cd.yml` has no SA to impersonate, and nothing can write to `web` or
   update the service. That change belongs in infra `web/`.

   The design to check there, not a verdict: the provider maps
   `google.subject = assertion.sub`. That lets the deploy SA bind to the
   subject `repo:indie-runners/indie-runners-web:environment:production`
   rather than to the repo-wide principal set. Then only a job that
   passed the approval can get deploy credentials, and a branch that
   drops `environment:` from the job gains nothing. Bound repo-wide, the
   environment is only a gate in the UI. The push SA can stay repo-wide,
   because pushing an image moves no traffic.
2. **`deploy.sh` still builds.** Sequence 5 reduced the `run deploy`
   flags. `deploy.sh:83` is still `gcloud builds submit --tag "$IMAGE"`.
   After this ticket the script builds nothing. It takes the image ref
   as an argument and deploys it. The header's "Version" paragraph
   ("deploys an untagged image … no version stream here") stops being
   true and gets rewritten.
3. **There are no tags.** `git tag` prints nothing. The convention is
   the CHANGELOG version, `1.9.N`, and the image tag is the same string.
   Job 2 can't read job 1's outputs, because a `workflow_dispatch` is a
   separate run. It takes the tag as an input, so the operator names
   what goes live.
4. **`.env.example` has no image line.** Its only near match is
   `# Tile images`, and the app never reads an image path. The stale
   current-tense line is `docs/ARCHITECTURE.md:536`: "built via Cloud
   Build and stored in `gcr.io/…`". `CHANGELOG.md:1199` and W-008 were
   true when written, so leave them (W-053's ruling).

## Acceptance

1. `.github/workflows/cd.yml`, on a tag push. It has
   `permissions: id-token: write, contents: read` set **on each of its two
   jobs**, not workflow-wide (amended 2026-10-29). It authenticates
   through the WIF provider as the push SA, runs `docker build` in the
   runner and pushes
   `europe-west1-docker.pkg.dev/indie-runners-dev-470411/web/indie-runners-web:<tag>`.
   Nothing in the repo calls `gcloud builds` any more (grep, quoted).
   Shown by a tag run that pushes without deploying, and the image is
   listed in `web`.
2. A second job, `workflow_dispatch` with a `tag` input, bound to
   `environment: production`. It authenticates as the deploy SA and runs
   `scripts/deploy.sh` with that digest (amended 2026-10-28). The rollback lines it prints
   show up in the run log.
3. After one real deploy through the workflow (approved by Paulo),
   `./scripts/deploy.sh --check` from Paulo's laptop names the same
   serving revision the workflow reported. Both outputs are quoted here,
   and `/` answers 200.
4. `docs/ARCHITECTURE.md` (Deployment) and the `deploy.sh` header say the
   image is in the `web` Artifact Registry repo, tagged with the release,
   built by `cd.yml`. CHANGELOG entry as usual.

## Out of scope

- **Retention on `web`.** A separate small ticket, once there's an image
  count to look at (Paulo).
- **Retiring `gcr.io`.** That's infra's. It waits until a post-switch
  revision is the rollback target (W-053, Out of scope).
- **W-008, the revision label.** The deploy step is where it would go,
  but it's still blocked on infra's `ignore_changes`. A tagged image
  already traces a revision to a release.
- **I-009, who owns traffic.** The rollback text `deploy.sh` prints stays
  as it is.
- **A laptop build path.** `cd.yml` is the only builder. A local
  `docker build` fallback is a separate decision if one is ever needed.
