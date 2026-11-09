# W-101 — The Crews jump hides "Create a crew", and the empty calendar has no box

`priority: 2` · `effort: S` · `area: templates` · `deploy: immediate`
`source: docs/IDEAS.md 2026-11-04 (Paulo, crews arc, highest priority), items 1 and 2`

## What is wrong

Two empty states on the own profile.

1. The nav's Crews link lands a runner with no crews on `#crews`, and on
   mobile the section head ("My crews" and "Create a crew") sits above
   the fold. They see only the empty box and must scroll up to find the
   button the box tells them to use.
2. The calendar's empty text is a bare paragraph, while the crews one
   sits in a box. Paulo wants the calendar's in the same box.

## Evidence

Paulo, from `docs/IDEAS.md`:

> On mobile it jumps straight to the My crews section. A first-time user
> sees "You're not in any crews yet. Create one, or ask a friend for an
> invite link." and has to scroll up to find "Create a crew".

> "No races on your calendar yet" should sit in a box, like the "You're
> not in any crews yet" message.

The likely mechanism, read from source and not yet seen in a browser.
The button is already in the section head, but the header is sticky and
nothing offsets an anchor jump (no `scroll-margin` or `scroll-padding`
anywhere in `static/css/`):

```
app/main.py:731            return RedirectResponse(f"/profile/{current_user.id}#crews", status_code=303)
app/templates/profile.html:100  <section class="profile-section" id="crews">
app/templates/profile.html:103      <a href="/crews/new" class="crews-cta">Create a crew</a>
static/css/main.css:30     height: 68px;      (the header)
static/css/main.css:34     position: sticky;
```

```
app/templates/profile.html:119  <div class="crews-empty">
app/templates/profile.html:140  <p class="profile-empty">No races on your calendar yet. Find one and mark yourself going.</p>
app/templates/profile.html:142  <p class="profile-empty">No races on this calendar yet.</p>
```

## Acceptance

1. Signed in with no crews, at 375px wide: Crews in the drop-down lands
   with "My crews" and "Create a crew" visible below the header, with no
   scrolling. Same at desktop width.
2. Default, veto at review: Paulo's first option, the jump lands higher.
   The button stays in the section head. If the mechanism above turns out
   wrong, say what it was in the changelog.
3. The leave flash (`/profile/<id>?left=…#crews`) also lands with the
   section head visible, since it uses the same anchor.
4. Both calendar empty texts, own and someone else's, sit in the same
   box as the crews one, same look.
5. A profile with races and crews renders as before. Anon: `/profile/<id>`
   still answers as before (W-085's ticket, not this one).

## Out of scope

- Moving "Create a crew" under the box (Paulo's second option), unless
  the review vetoes the default.
- The calendar's format. That is W-098, which keeps this box.
- Any other empty state ("Been there", the crew hub).

## Verdict

**VERDICT: APPROVED** — 2026-11-04. Reviewed `fix/profile-empty-states`
at `1322f99`. The changelog names the wrong belief, its cost, the new
belief and the measurement. The mechanism held: the nav is `height: 68px`
at every width (the 600px query changes padding only), so one
`scroll-padding-top` covers mobile and desktop. Read on the branch: no
template links to a fragment, nothing in `static/` scrolls, and
`.profile-empty` had no other user. Verified from the worktree
(`/proc/<pid>/cwd` → `irw-W101`), signed in and anon. Ticket is
`deploy: immediate`. No routed check: nothing in the request log
changes.

Dropped, with reasons:
- TODO's "Disproved" line says a profile with nothing on it "never" had
  the head hidden. That was measured at one height, 725px, and Paulo saw
  it on a phone. The changelog scopes it correctly ("a shorter phone
  viewport scrolls further"), and TODO is overwritten by the next ticket.
  The fix covers both cases either way.
- TODO lost its "Last true" header line. The title still names W-101,
  and the next ticket rewrites the header.

**Not verified:**
- A real phone. The landing was measured in headless Chrome at 375px and
  1280px, 725px tall, with smooth scrolling off. Mobile Safari's handling
  of `scroll-padding-top` on a fragment jump has not been seen. Settled
  by Paulo tapping Crews on his phone after deploy.
- The leave flash's landing. It rendered with `?left=`, and it uses the
  same anchor, but its scroll position was not measured.
- The `/crews` 303 followed in a real browser. The fragment was
  re-triggered on saved HTML; the redirect itself is unchanged.
