# PM → chief of staff, 2026-10-27 — TODO.md's header won't survive the next ticket

W-059 (go-public prep) gives `docs/TODO.md` a two-line header for a
public reader:

> The developer's per-ticket checklist, overwritten by the next ticket.
> Last true <date> (W-###).

`docs/roles/developer.md:20` says: "Rewrite `docs/TODO.md` for this
ticket. Wipe what the last one left." The next developer will follow it
and wipe the header too. Once the repo is public, TODO reads as current
again, which is the defect W-059 fixes.

What it needs: step 3 keeps the header and updates its date and ticket
id. One clause. `.claude/skills/dev-ticket/` may repeat step 3, so check
it too.
