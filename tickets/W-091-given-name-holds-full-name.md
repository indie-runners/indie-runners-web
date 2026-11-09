# W-091 — An account with its full name in the first-name field still shows the full name

`priority: 1` · `effort: S` · `area: services` · `deploy: immediate`
`source: W-090 review 2026-11-01 (PM, run against the branch's helper)`

**THE NEXT TICKET, after W-090 merges.** The defect is in W-090's
spec, which the PM wrote: acceptance 1 said *"No `family_name` →
`given_name` alone"*, assuming a given name is one name.

## What is wrong

`short_display_name` returns `given_name` unchanged when `family_name`
is missing or blank. A Google account whose owner typed their whole
name into the first-name field and left the last name empty sends
exactly that, so W-090's goal fails for them on every sign-in.

## Evidence

The branch's helper, `fix/names-first-plus-initial` at `3fc1979`, run by
the PM on literals:

```
{'given_name': 'Paulo Morales'}                                -> 'Paulo Morales'
{'given_name': 'Paulo', 'family_name': '  '}                   -> 'Paulo'
{'given_name': 'Ana María', 'family_name': 'García López'}     -> 'Ana María G.'
```

The first line is the defect. The third is fine: two given names and a
last initial. How many accounts have this shape is not measurable:
`web.users` keeps only the derived column, and that is by design.

Migration 015's header says *"the file can be re-run"*. On a
literal the PM ran read-only, a short form with two given names is
shortened again:

```
'Ana María G.'  touched=True  -> 'Ana G.'
```

Harmless, still short, but the claim is wider than the guard.

## Acceptance

1. No usable `family_name` and a multi-token `given_name` → the
   `name` rule applied to `given_name`: first token, last initial,
   `.`. `{'given_name': 'Paulo Morales'}` → `Paulo M.`.
2. One more assert for that case in the `__main__` block.
3. Migration 015's header says *run once*, not *re-runnable*, if 015
   has not yet been run when this merges. If it has, leave the file
   alone and say so in the changelog.
4. Changelog entry: the wrong belief is the PM's (a given name is one
   name).

## Out of scope

- **Surname particles.** `family_name: 'de Wit'` gives `d.`, while 015's
  backfill of `Anne-Marie de Wit` gives `W.`. A backfilled user flips
  at their next sign-in. That is cosmetic and both are short. Paulo can
  ask for it.
- **Rows already stored.** A sign-in rewrites them; 015 covers the rest.
- **Non-Latin scripts.** `李 王.` and `Пётр И.` are what the rule
  produces. No complaint has been made.

## Verdict

**VERDICT: BLOCKED — R1** — 2026-11-01, reviewing
`fix/given-name-holds-full-name` at `e0a2d40`. The helper is right:
the PM ran it on eight literals, including a blank `family_name`, a
blank `given_name` with `name`, and `Ana María` + `García López`, and
each gives the short form the ticket asks for. Seven asserts, both
write sites unchanged. The changelog names the wrong belief as the
PM's, its cost and the new rule. `dev.sh` was proved to serve this
worktree (`/proc/<pid>/cwd`), and the changelog does not claim a
render it could not make. Docs: 31 added lines.

**R1.** `docs/ARCHITECTURE.md:133` still states W-090's rule: *"from
Google's `given_name`/`family_name`, falling back to `name`'s first
and last tokens"*. That is the belief this ticket corrects, in the
contract a future developer reads first. Unblocked when that sentence
says: given name + family initial when both are present, else the
first and last tokens of `given_name`, else of `name`. Its *"until it
runs"* clause about 015 goes too, or is dated, if 015 has run.

Routed check 41 is amended now, not at re-review: gate (c) is W-091's
revision, and a long name written between 015 and (c) is residue, not
a regression. R1 is docs-only, so the prediction does not change.

**Not verified:** a real Google sign-in through 1.9.57. The write path
is proved by asserts, as in W-090. Also not verified: that Paulo ran
015. The changelog and TODO say so, but nothing in the repo records
it. If 015 has **not** run, acceptance 3 applies and its header must
say *run once* before merge.

### Re-review

**VERDICT: APPROVED** — 2026-11-01, reviewing
`fix/given-name-holds-full-name` at `09c8821` (rebased on master; the
code is byte-identical to `e0a2d40`). R1 resolved: ARCHITECTURE § web.users
states the rule as shipped (both present, else `given_name` tokens,
else `name` tokens), and the 015 clause is dated instead of
conditional. Docs: 32 added lines. Routed check 41 already carries
gate (c); nothing new to route. Ticket is `deploy: immediate`.

**Not verified:** unchanged from above. A real sign-in through 1.9.57,
and Paulo's own word that 015 ran. ARCHITECTURE now states it as fact
on the developer's report. If it is wrong, 015's header needs *run
once* and that sentence goes back to conditional.
