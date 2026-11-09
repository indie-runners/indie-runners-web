# W-015 — `tickets/BACKLOG.csv` is CRLF, and a one-cell edit reads as a whole-board rewrite

**Priority:** 4 · **Effort:** S · **Area:** hygiene · **Deploy:** batched
**Source:** `docs/DEV_NOTES.md` 2026-08-28 (while on W-007) — the note asks
the PM to decide; this is the decision

## What is wrong

The board is the one file **two roles write to**, and its line endings
make an innocent edit indistinguishable from a boundary violation.

From the developer's note:

> The file has **CRLF** line endings; every other tracked text file in the
> repo is LF. A read-modify-write in Python (`open(p).read()` →
> `open(p,'w').write(...)`) silently normalises them, so a **one-cell edit
> came back as a 14-line diff** — the whole board rewritten, which is
> exactly the shape of "someone crossed the single-writer line" that
> `docs/roles/README.md` says a conflict on this file means. It is not; it
> is an encoding artefact, and it would have cost the reviewer real time.

That is the defect, and it is not cosmetic. `docs/roles/README.md` says:

> A conflict on this file means someone crossed the line.

The single-writer rule is enforced by **reading the diff**. An encoding
quirk that turns every edit into a full-file diff destroys the signal that
rule depends on — the reviewer either loses time proving it was innocent,
or stops looking, which is worse. The developer caught it only because the
diffstat said 28 lines for a two-field change.

## Why it is p4 and not p5

It is tooling hygiene, so nothing user-facing — but unlike W-004 and
W-009 it degrades a **control**, and it will recur on every single edit by
either role until it is fixed. That is a standing tax on the reviewer's
attention, not a one-off annoyance.

## Acceptance

1. `tickets/BACKLOG.csv` is LF, matching every other tracked text file.
2. **The conversion commit contains nothing else.** It is a 14-line
   whole-file diff by necessity, and it must be trivially recognisable as
   the conversion and only the conversion — a content change hidden inside
   it is exactly the failure this ticket exists to prevent.
3. `git diff --check` no longer reports trailing whitespace on every line
   of the file. Per the note, that report is the CR and not real
   whitespace; it disappearing is the confirmation.
4. **A subsequent one-cell edit produces a one-line diff.** Demonstrated,
   not assumed — make a trivial edit, check the diffstat, revert it.
5. **Prevented from regressing**, since both roles edit this file with
   different tools. A `.gitattributes` entry (`*.csv text eol=lf`, or
   scoped to this path) is the obvious mechanism; name what you chose and
   why. Without this, the next writer whose editor guesses CRLF undoes
   the ticket silently.

## Out of scope

- **Any content change to the board.** No re-wording, no re-prioritising,
  no status or branch edits riding along. See acceptance 2.
- **Other files' line endings.** The note says every other tracked text
  file is already LF; this ticket does not go looking, and a repo-wide
  normalisation is a different change with a much larger diff.
- **Changing the board's format** — CSV stays CSV. The single-writer
  column rule is built on it.
- **The single-writer rule itself.** It is correct; this ticket restores
  the diff signal it relies on.

## Verdict

**VERDICT: APPROVED** — 2026-10-27. All five acceptance points re-checked
read-only against the branch: `12c57f1` is 42+/42- on the board alone and
`git diff --ignore-cr-at-eol` over it is empty (acceptance 2); the branch
blob has zero CRs (1, 3); `.gitattributes` is scoped to the path, and
`tickets/BACKLOG.csv` is the only tracked CSV, so the scoping loses
nothing (5); both status commits are 1+/1- on the board (4, on real
edits). The changelog records that the premise was wrong in shape
(`i/mixed`, not all-CRLF) and right in effect. Master has not moved since
the merge base, so the merge is clean. Docs: 28 lines added. No app code
was changed, so there was no render to check and nothing to deploy. It
predicts nothing in production, so there is no routed check.

**Not verified:** an *existing* checkout after the merge. Each worktree
or clone that holds the old mixed-ending working copy has to pull it once
before the attribute protects it. A `git status` showing the board as
modified with no visible diff, straight after pulling, is this case and
not an edit. Python's `csv.writer` defaults to `\r\n`. A PM or developer
script that writes the board with it was covered only through the
developer's whole-file CRLF rewrite, not by running that writer itself.
