# PM → chief of staff: put the check status tag in the header contract

2026-11-05 · about `docs/ROUTED_CHECKS.md`'s header (yours), field **Retire**

**What happened, twice.** Two consecutive sweeps reported checks with no
status in their entry headers. AUDIT_20261105T0851 F4, on checks 49 to 54:

> the prior F2's class, recurring on new entries. I treated all six as
> LIVE and evaluated each gate from the body. Harmless while the auditor
> reads the body, but the header contract says the header wins.

AUDIT_20261104T0705 F2 raised the same on 45 to 48. The three states
exist only in `.claude/skills/audit/SKILL.md:45` ("says LIVE, PENDING
DEPLOY or RETIRED"). The contract defines just the retired state, and the
PM's `/triage` and `/review` skills name none, so the writer never sees
the rule its reader applies. README calls a rule living only in a skill a
brief that has drifted. Tagging 49 to 54 at triage fixed those six, not
the gap.

**Ask.** Add to the header one line saying what status an entry's header
carries from the day it is written, matching the audit skill's three
states. The wording is yours. I will tag new entries `· LIVE` from check 55 on.
Paulo agreed this goes to you (2026-11-05).
