# W-008 — A deployed revision carries no reference to the commit it was built from

`priority: 4` · `effort: S` · `area: deploy` · `deploy: batched`
`source:` `docs/DEV_NOTES.md`, 2026-08-28, written while on W-001

## What is wrong

The image is pushed **untagged** to `gcr.io/…/indie-runners-web` and
overwritten on every deploy, and nothing labels the Cloud Run revision. So
the revision — the only durable handle on what is serving — cannot be
traced back to a commit by anything except the memory of whoever ran the
deploy.

W-001 fixed the near half of this: `deploy.sh` now prints the deploying
SHA as it runs. That serves the operator **watching the deploy**. It does
nothing for the person asking, three weeks later, *what is actually
serving right now* — which is the question a rollback decision turns on,
and the only moment anyone asks it is a bad one.

## Evidence

From `docs/DEV_NOTES.md`, verified by the developer against a live
revision while building W-001:

> **The deployed revision is not traceable to a commit.** Verified while
> building W-001: `gcloud run revisions describe indie-runners-web-00050-6xt`
> carries no reference to the git SHA it was built from, because the image
> is pushed untagged and nothing labels the revision. W-001 makes the
> script *print* the deploying SHA, which helps the operator watching it
> run, but does not help anyone asking later "what is actually serving?".
> A `--labels=commit=$(git rev-parse --short HEAD)` on the `gcloud run
> deploy` would close that, and it is one flag. Out of scope for W-001,
> whose brief is the three named guards, and it touches the deploy flags
> the ticket said to leave alone. Worth a ticket.

The developer drew that boundary correctly and it is upheld here: W-001's
brief was the three named guards, and its TODO listed "not touching the
`gcloud run deploy` flags themselves" as deliberate. This ticket is the
follow-up that boundary implies, not a reopening of it.

The 1.9.4 changelog already states the underlying condition, without
drawing this conclusion from it:

> The image is pushed untagged to `gcr.io/…/indie-runners-web` and
> overwritten on every deploy, so the image reference identifies nothing
> after the fact. The Cloud Run *revision* is the only durable handle on
> what was serving.

That reasoning is right and stops one step short. A durable handle that
points at no source is only half a handle.

## Why p4

Nothing is broken and no user can see it. It is **recoverability** — it
matters only at the moment something else has already gone wrong, and it
must be in place *before* that moment to be worth anything. That is p4
work: not urgent, and worthless if done reactively.

## Amended 2026-10-26: I-006 landed first

`indie-runners-infra` I-006 is applied (`32bea99` here). `deploy.sh`'s
`gcloud run deploy` is now `--image` plus region/project/platform, and
everything else about the service's shape lives in
`indie-runners-infra/web/service.tf`. That file's `lifecycle.ignore_changes`
lists the image, `client` and `client_version`, and no labels. So a label
set at deploy time will show as drift on the next infra plan, and an
apply would strip it. The I-006 entry in `docs/IDEAS.md` says the infra
side "needs the same `ignore_changes`".

**Order:** the infra change goes first. That is the labels attribute(s)
`gcloud run deploy --labels` writes on whatever resource `service.tf`
declares. The infra developer checks which ones; this ticket does not
guess. That is infra's work, and Paulo routes it, because the web PM has
no write there. **Do not merge until it has landed:** once the flag is on
`master`, the next deploy for any ticket is a labelled one.

## Amended 2026-10-28 (triage): infra I-016 goes first, and the flag is unnamed

From `docs/IDEAS.md` (infra triage 2026-10-27 (2), item 2):

> Paulo: the label goes on the **revision**, so infra ignores
> `template[0].labels`. W-008 says `--labels=commit=…` and leaves the
> attribute to infra. **Before either ticket lands, name the flag here.**
> If `gcloud run deploy --labels` also writes service-level labels, either
> infra ignores both or W-008 uses a revision-only flag. I-016's developer
> quotes `--help` and answers here.

So the infra change above is I-016, and the flag in acceptance 1 is an
example, not a decision. Don't start until I-016's answer is in
`docs/IDEAS.md` and I-016 is applied. Use the flag that answer names.

## Acceptance

- `scripts/deploy.sh` passes a commit label on `gcloud run deploy`, e.g.
  `--labels=commit=$(git rev-parse --short HEAD)`. The dirty-tree guard
  already runs before this point, so the SHA is guaranteed to describe the
  code in the image — **say so in the changelog**, because that guarantee
  is the whole reason the label can be trusted, and it is W-001's guard
  doing the work.
- **Verification is split from the code change, deliberately.** A Cloud
  Run label can only be observed on a real deploy, and `deploy: batched`
  means this ticket does **not** justify one. So:
  - before merge: `bash -n` parses, and `--check` still runs read-only and
    unchanged;
  - at the next deploy, whenever it happens for another reason: confirm
    with `gcloud run revisions describe <rev> --format="value(metadata.labels)"`
    that the label is present and matches. **Record the result then, in
    that release's changelog entry** — not as a claim made in advance here.
  - The changelog for *this* ticket must state plainly that the label is
    unverified against a live deploy at time of writing. An untested guard
    described as working is the exact defect this repo's review asks about.
- Label constraints are checked, not assumed. Cloud Run label values are
  restricted (lowercase alphanumeric, `-` and `_`, 63 chars). A short SHA
  is lowercase hex and safe — confirm rather than assume, and note it.
- The changelog names the `indie-runners-infra/web/service.tf` change
  this relies on, and that it landed before the first labelled deploy.
- `docs/CHANGELOG.md` version bumped.
- `docs/ARCHITECTURE.md` — the deploy contract already records
  rollback-by-revision from W-001. Extend it: a revision now names its
  commit, so the rollback target can be read back to a diff.

## Out of scope

- **Tagging the image.** Labelling the revision is one flag; moving to
  tagged images changes what `gcloud builds submit` pushes, what a rollback
  refers to, and re-opens the version-stream question 1.9.4 deliberately
  closed. If tagged images are wanted, that is its own ticket with that
  argument made explicitly.
- **Any other `gcloud run deploy` flag.** One flag, this flag.
- **Backfilling labels onto existing revisions.** They were built from
  commits nobody recorded; a label invented after the fact is a guess
  wearing the costume of a fact. The label starts being true from the next
  deploy forward.
- **Triggering a deploy to verify.** `deploy: batched`. See acceptance.
