# W-080 — Crew member names don't open their profiles, and the invite box doesn't say how to use it

`priority: 2` · `effort: S` · `area: templates` · `deploy: immediate`
`source: docs/IDEAS.md 2026-10-31 (Crews v1 spec, build steps 4 and 5); folds in W-042`

**Crews arc, step 4. After W-092 (Paulo, 2026-11-02).**

**AMENDED 2026-11-02 (Paulo): the "Next: {race}, {date}" line per
member is dropped. "We do not want that." What remains is W-042's
profile links and the invite box wording.**

## What is wrong

The sidebar's Members list (W-077 moved it there unchanged) shows avatar,
name and an Admin tag, as plain text. W-042 asked for the names to open
the member's profile. The invite box's help text doesn't say how the
link is meant to be used.

## Evidence

Spec, § Sidebar (the "Next:" clause struck by Paulo, 2026-11-02):

> - Members box: list of members with initials avatar, name~~, and "Next: {race}, {date}" being their soonest going race, or "Nothing confirmed yet"~~.
> - Invite box: readonly input with the invite URL and a Copy button. Short explanation: share this link in your group chat, anyone who opens it and signs in joins the crew.

Step 5 (invite token, join route, invite box) is mostly live already. `crews_detail.html` today:

```
      <p class="settings-help">
        Share this link with anyone you want in the crew. It works for
        anyone who has it, so treat it like a password.
      </p>
      <div class="crew-invite-box">
        <input id="crew-invite-input" type="text" readonly value="{{ invite_url }}">
        <button type="button" id="crew-invite-copy" class="settings-submit">Copy</button>
```

W-042 (open, p4): *"make peoples profile in listing of members of crews clickable"*. Its decision 1 ("`private` members stay plain text") lapses with W-076: every crew-mate can open every member's profile.

## Acceptance

1. Each member row: avatar and name as one link to `/profile/<id>` (W-042's decisions 2 and 3), the Admin tag as now.
2. The invite help text says the spec's sentence. It keeps a short "anyone with the link can join" warning: the link has no expiry.
3. Verified signed in on a crew with at least two members. Each name opens a profile that returns 200. Anon on the crew page is unchanged (W-085 owns that).

## Out of scope

- **A per-member "Next: {race}" line.** Dropped by Paulo 2026-11-02. Not to be built.
- The small-crew hint ("Small crews may reveal who is going"). Unchanged.
- Rotation, still admin-only. Nothing Paulo said changes it.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-093** — 2026-11-02. One ticket,
in scope: the member row is one link, the Admin tag sits outside it, and
the invite text says the spec's sentence plus the no-expiry warning. The
"Next:" line is correctly absent. Changelog 1.9.60 names the wrong
belief, cost, new belief and evidence; docs +34 lines. The worktree
check (`/proc/<pid>/cwd`) rules out W-009. Ticket is `deploy: immediate`.

The claim that every member's profile opens for a crew-mate was checked
in code, not from the 200s. Migration 014 left only `public` and
`crews_only` under the CHECK. `_can_view` returns True for both when
viewer and target share a crew, and every row on this page shares it.

**Not verified:**
- The 16 profile bodies were not checked as `profile.html` rather than
  `profile_hidden.html`. Both answer 200 by design, so acceptance 3 as
  the PM wrote it could not tell them apart. The code path above settles
  it.
- The browser render. The changelog evidences markup only; TODO asserts
  "16 real rows render fine". Nothing says whether any of the 16 lacked
  an `avatar_url`, so the initial-avatar branch inside the link may
  never have rendered.
- A real sign-in. The signed-in tier used a minted cookie.
- A member with no `display_name` renders the link text "None". This
  predates the branch: W-093.
