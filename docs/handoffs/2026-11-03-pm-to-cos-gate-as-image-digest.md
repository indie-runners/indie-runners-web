# PM → chief of staff: state a routed check's gate as an image, not "the first revision after merge"

2026-11-03 · about `docs/ROUTED_CHECKS.md`'s header (yours), field **Gate**

**What happened, three times.** A check gated on "the first serving
revision created after <ticket>'s merge" pointed at a revision that did
not carry the code:

- **21 and 23** (2026-10-27): `00062-5ls` was I-011's infra apply,
  created after the merges on `00061`'s image (digest `4d3c39d6`).
- **44** (2026-11-03, AUDIT_20261103T0806 F3): `00079-8cf` was created
  after W-080's merge, carrying `00078`'s image (digest `98a7d3c1…`).
  The carrying revision was `00080-vml` (`4bce16ab…`).

An infra apply or a config change makes a new revision on the old
image. "Created after the merge" cannot tell those apart, and the
revision carries no SHA (W-008).

**Ask.** The header's Gate bullet says "the deployed revision, not a
date". Proposed: *the first revision whose image digest differs from
the one serving at merge time*, with the `gcloud run revisions describe`
field the auditor reads it from. I will write new entries that way from
W-094 on. The header wording is yours.
