# W-081 — The only way out of a crew is deleting your account

`priority: 2` · `effort: S` · `area: services` · `deploy: immediate`
`source: docs/IDEAS.md 2026-10-31 (Crews v1 spec, build step 6) + 2026-10-30 (leaving a crew, Paulo)`

**Crews arc, step 5. After W-078,** because leaving lands on the profile's My crews.

## What is wrong

`CrewService` has `add_member` and nothing that removes one. Spec rule 5:
*"If someone does not want a crew to see their plans, they leave the
crew."* Today they can't.

## Evidence

Spec routes: `POST /crews/{slug}/leave        remove membership, redirect to profile`.

The trap, from W-022's spec, quoted in IDEAS 2026-10-30: *"no route lets a creator leave their crew. A future 'leave crew' or 'remove member' ticket makes it reachable and must hand over `created_by` itself."*

`user_service.py:85-88`, the existing hand-over:

```
        and crew_invites.created_by are soft refs with no FK, so each crew
        the user is in either goes (no one else in it) or passes to the
        longest-standing remaining member, admins first.
```

and the check that 500s if a soft ref is left behind (`:113-121`):

```
        if leftover:
            self.db.rollback()
            raise RuntimeError(f"user {user_id} still referenced by {leftover} crew/invite rows")
```

W-031 moves the delete route's Origin check into `SameOriginMiddleware`, which refuses any cross-origin non-GET request (AMENDED 2026-11-01, W-031 review). Merge after W-031, and this route is covered with no inline check. It matters here because a cross-site leave by a crew's only member deletes the crew, which can't be undone.

## Acceptance

1. One method holds the hand-over. Both `delete_account` and leave call it, so the two ways out behave the same: the last member leaving deletes the crew; otherwise `created_by` on the crew and its invites passes to the longest-standing remaining member, admins first, who becomes admin.
2. `POST /crews/{slug}/leave`: member only, Origin checked by W-031's middleware (no inline check), 303 to the profile with a flash naming the crew.
3. The hub's sidebar has a Leave button. Its confirm text says plainly when leaving will delete the crew (only member).
4. After leaving: the crew page shows `crews_hidden.html`, and the user's `crews_only` attendance is no longer visible to former crew-mates they share no other crew with.
5. Verified signed in, four cases: a plain member leaves; the creator leaves a crew with an admin left; the creator leaves as the only admin (the heir is promoted and owns `created_by`); the only member leaves (the crew is gone). After the creator's leave, **that user's account deletion succeeds**. That is the 500 this ticket must not create.

**Confirmed by Paulo, 2026-10-31:** the last admin leaving hands the crew over by the same rule, rather than refusing until they promote someone. No promote UI exists.

## Out of scope

- An admin removing someone else (W-082).
- Rejoin: a member who left can rejoin with the link, like anyone holding it.

## Verdict

**VERDICT: APPROVED** — 2026-11-03. The seven checks pass. One method,
`CrewService.remove_member`, holds the hand-over, and `delete_account`
loops over it, which meets acceptance 1. All four leave cases and the
creator's account deletion afterwards were run from the W-081 worktree
(cwd checked), each confirmed in the DB. The route is gated like rotate
(anon `401`, non-member `404`, cross-origin `403`). The `?left=` flash
sits inside `viewer_is_self`, so the anon tier never renders it. Docs
are 58 lines. `deploy: immediate`. Routed check 47.

**Not verified:**
- The browser `confirm()` dialog itself. The hub HTML was read, and both
  texts render. Paulo placed the button himself (87943b3), so he has seen
  the hub, though not necessarily the dialog.
- After the leave, `GET /crews/<slug>` for the leaver. This is the
  existing member gate, unchanged, but acceptance 4 names it and nothing
  requested it.
- Whether the profile flash was looked at, or only the `303` Location.
- Two members of a two-person crew leaving in overlapping transactions.
  Each deletes its own row and names the other as heir. That leaves a
  crew with no members, and the survivor's later account deletion hits
  the leftover check: rolled back, logged, no data lost. The same race
  already existed in `delete_account`. Routed check 47's invariant query
  would show it; not filed.
