# W-082 — A crew admin can't remove a member

`priority: 2` · `effort: S` · `area: services` · `deploy: immediate`
`source: docs/IDEAS.md 2026-10-31 (Crews v1, Paulo's decision 2) + 2026-10-30 (removing someone from a crew)`

**Crews arc, step 6. After W-081,** whose membership-removal method this reuses.

## What is wrong

Admins exist (`crew_memberships.role`) but can only rotate the invite link.
Paulo: *"The admin/creator is just one more member that is able to remove
others, that's it."* This was not in the spec's In list. Decision 2 adds it.

## Evidence

Paulo, decision 2: *"I just would like for members to be able to spread the link and to leave the crew if they want. The admin/creator is just one more member that is able to remove others, that's it."*

The 10-30 entry's open points, unanswered by Paulo:

> 1. **The last admin leaves:** hand the crew over by the same rule as account deletion, or refuse until they promote someone?
> 2. **Can an admin remove another admin?**
> 3. **Rotate the invite link automatically when someone is removed**, or leave that to the admin?
> 4. **Does the removed member find out?**

(1 is W-081's default.)

The invite link has no expiry and can be reused (`crew_invites`: no `expires_at`), so a removed member who still has it can rejoin.

## Acceptance

1. `POST /crews/{slug}/members/{user_id}/remove`: the actor is an admin of the crew, the target is a member and not the actor (that is leave), Origin checked by W-031's `SameOriginMiddleware`, no inline check (AMENDED 2026-11-01, W-031 review). Otherwise 403/404.
2. The removal goes through W-081's method, so a removed creator hands over `created_by` the same way.
3. Each other member's row in the sidebar has Remove, for admins only. After a removal, the flash says the person can rejoin with the current link and offers Rotate.
4. Verified signed in: an admin removes a member; an admin removes another admin (who is the creator, so the hand-over runs); a plain member's POST is refused; an admin's POST on themself is refused. The removed user gets `crews_hidden.html`.

**Confirmed by Paulo, 2026-10-31:** (2) an admin can remove another admin, since he described admins as "just one more member"; (3) no automatic rotation, because rotating breaks the link already shared in group chats, so the flash offers it; (4) no notice, since notifications are out of v1.

## Out of scope

- Promoting or demoting (role management UI is out of v1).
- Blocking a removed user from rejoining. Nothing records a removal.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-093** — 2026-11-03. The seven
checks pass. The route reuses `CrewService.remove_member` unchanged, which
meets acceptance 2. Because the acting admin stays and the heir query puts
admins first, the heir on this path is always already an admin: no one is
promoted by a removal, and the crew cannot be deleted. All four acceptance-4
cases were run from the W-082 worktree (cwd checked), plus anon `401`,
cross-origin `403`, unknown target and slug `404`, and the removed
member's `crews_hidden.html`. The creator hand-over was confirmed in the
DB on crew and invite. The hub is signed-in only, so the anon tier is the
`401` alone. Docs are 50 lines. `deploy: immediate`. Routed check 48.
W-093 is amended to cover the two new raw `display_name` renders.

**Not verified:**
- The browser `confirm()` dialog. The changelog says so.
- The Rotate button inside the removed flash. It rendered and was never
  clicked. It posts to the existing rotate route, so risk is low.
- The member row's look. Avatar, name, Admin tag and Remove share one
  flex row in a narrow sidebar. The HTML was read, and nobody has seen
  it in a browser. Paulo placed W-081's button but not this one.
- Two admins removing each other in overlapping transactions. Each
  deletes the other's row and names itself heir, which leaves an empty
  crew. Same shape as the W-081 race already accepted. Routed check 48
  shows it. Not filed.
