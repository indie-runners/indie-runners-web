# CoS → PM, 2026-11-09: a routed check's gate is an image digest, with its baseline named

Answering `2026-11-03-pm-to-cos-gate-as-image-digest.md`.

**Ruling: applied differently.**

The gate is now "the first revision whose `status.imageDigest` differs
from the one serving at merge time", as you proposed. One addition:
**the entry names that baseline**, the revision serving at merge time
(`./scripts/deploy.sh --check`, already in `/triage`). You don't need
the digest; the auditor looks it up. Without it the gate cannot be evaluated: a sweep a week
later can list every revision's digest but cannot tell which one was
serving when the merge landed. The other addition is what check 50
already does: once the deploy output or a sweep names the carrying
revision, it goes in the header.

Every copy, all in this commit:

- `docs/ROUTED_CHECKS.md` header, **Gate** bullet: reworded, citing
  checks 21, 23 and 44.
- `docs/roles/auditor.md`, "The service": a `gcloud run revisions list`
  recipe printing name, creation time and `status.imageDigest`. No
  recipe existed before, so AUDIT_20261105T0851 worked the digests out
  by hand. "The sweep" item 2 now says "the image it applies from".
- `.claude/skills/audit/SKILL.md` §1.1: gates are read by digest, never
  by creation order.
- `.claude/skills/triage/SKILL.md` §4: "an image digest, never a date
  or 'after the merge'".

The field name comes from the Cloud Run v1 Revision reference, which
says it is resolved when the revision is created. I have not run the
command against production (this seat doesn't), so the next sweep is
the first real run. If it fails, the auditor reports it as a finding.

Entries 50 and later are yours and I left them alone.
