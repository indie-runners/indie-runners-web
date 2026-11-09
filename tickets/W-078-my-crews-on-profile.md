# W-078 — "My crews" lives on Settings, and nothing in the nav leads to a crew

`priority: 2` · `effort: S` · `area: templates` · `deploy: immediate`
`source: docs/IDEAS.md 2026-10-31 (Crews v1 spec, build step 2: profile section; Paulo's decision 6)`

**Crews arc, step 2. After W-077.** See `docs/PLAN.md`.

## What is wrong

The only list of a user's crews is a section on `/settings`. The nav menu
has My profile, Settings and Log out. Paulo's spec puts "My crews" on the
profile, with a "Crews" nav link.

## Evidence

Spec: *"Profile page gains a 'My crews' section: crew name, member count, link to hub, button to create a crew. If a user has exactly one crew the nav link 'Crews' goes straight to that hub, otherwise to the profile."*

Decision 6: *"with b"*: "My crews" moves to the profile, and the Settings crews block goes.

`base.html:42-44`:

```
        <a href="/profile" role="menuitem" class="nav-dropdown-item">My profile</a>
        <a href="/settings" role="menuitem" class="nav-dropdown-item">Settings</a>
        <a href="/auth/logout" role="menuitem" class="nav-dropdown-item nav-dropdown-item--logout">Log out</a>
```

`crews_detail.html:8`: `<a href="/settings" class="back-link">← Settings</a>`.

## Acceptance

1. Own profile (not preview, not someone else's) shows My crews: name, member count, link to the hub, Create a crew. Empty state keeps today's Settings copy.
2. The Settings crews section is gone. `_settings_context` stops loading crews.
3. The nav menu gains Crews: the hub when the user has exactly one crew, otherwise `/profile` (anchored to the section).
4. The crew page's back link points to the profile.
5. Verified signed in with zero, one and two crews; another user's profile shows no My crews; anon unchanged.

## Out of scope

- Showing a user's crews to *other* viewers of their profile.
- The visibility radio's wording (W-076).

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-087, W-085** — 2026-10-31. The
1.9.53 entry names the wrong belief (0.13.0's one surface for the knob and
its primitive, no `/crews` nav entry), what it cost (a member had to know
to open Settings to reach their crew), and Paulo's decision 6. The `GET
/crews` redirect has a reason a reader keeps: a per-user href in
`base.html` would put a crews query on every signed-in render. Verified
against this worktree (`/proc/<pid>/cwd`, not the W-009 trap): 0, 1 and 2
crews (users 1, 12, 26), a stranger's profile, preview, Settings, anon `/`,
1280 and 375 px. `list_crews_for_user` has two callers, both changed. The
create form's back link is outside acceptance 4 but follows from it (the
profile's button opens the form). Docs: 48 lines. ARCHITECTURE updated, no
new file.

W-087 is the developer's own DEV_NOTES flag: `crews_hidden.html` and
`crews_invite_invalid.html` still go back to Settings, which has no crews
now. W-085 is amended: anon `GET /crews` is a fourth bare 401.

**Not verified:** the member counts against the database. The changelog's
check is a `GROUP BY user_id`, which counts crews per user (the 0/1/2 the
test needed), not members per crew. The count is right by reading: the
subquery is correlated on `Crew` only, so it counts every membership of
that crew, and user 26's two crews show different numbers (2 and 1), which
a per-user count could not produce. A `GROUP BY crew_id` would settle it.
Also not seen: the `#crews` fragment landing in a real browser, the
dropdown open with the new item, `HEAD /crews`, and a user whose only crew
has the slug `new` (only possible if prod held one before W-049; `/crews`
would then open the create form).
