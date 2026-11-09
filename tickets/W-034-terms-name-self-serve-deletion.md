# W-034 — The terms still say deletion is by email only, and the privacy policy has no revision date

`priority: 2` (first in p2, on Paulo's call, 2026-10-23) · `effort: S` · `area: templates` · `deploy: batched`
`source: Paulo, 2026-10-23, after the W-022 re-review`

## What is wrong

W-022 adds a self-serve delete under Settings and updates privacy §8.
The terms were not touched. `terms.html` §9 Termination still reads:

> You may stop using Indie Runners and request deletion of your account
> at any time by emailing paulo@indierunners.co, as described in the
> Privacy Policy.

This is not false, since email still works. But it is the page a user
reads when they want to leave, and it doesn't mention the button.

The terms carry `Last revised: 27 July 2026` (`terms.html:14`), with a
maintainer comment on line 1 saying to update it on every change. The
privacy policy has no date at all, and W-022 changes what it promises
(§8: self-serve deletion, 7-day backups).

## Acceptance

1. Terms §9 says a user can delete their account themselves under
   <a href="/settings">Settings → Delete account</a>. It also keeps
   email as the other route. Wording is Paulo's: it is a legal page in
   his voice.
2. The terms' "Last revised" date is the date this merges.
3. `privacy.html` gets a `Last revised:` line in the same place and
   markup as the terms (`legal-footnote`, under the lede), dated the
   same day. It also gets the same maintainer comment on line 1.
4. Both pages render anon after the edit, and the Settings link from
   terms §9 opens the delete section for a signed-in user.
5. Changelog entry.

## Constraints

- **Merges after W-022, and ships in the same deploy.** The link points
  at a section that only exists on W-022's branch. Deployed before it,
  the terms would describe a button that is not there.
- Terms §11 promises that *material* changes are announced before they
  take effect. Adding a way to leave is not a material change to the
  user's obligations, so no advance notice is needed. If the wording
  ends up changing anything else in the terms, say so, because then §11
  applies.

## Out of scope

- Any other edit to either page, including privacy §6's silence on
  backups (W-032).
- A "what changed" history on the legal pages.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-035** — 2026-10-23, on
`f6e04f7`. The branch row says `review`. Docs budget: 42.

Every acceptance item is met. §9 adds the self-serve route and keeps
email. Both dates read 23 October 2026, and privacy got the footnote
and the maintainer comment. The changelog's §11 reasoning holds: adding
a way to leave changes no obligation. It was run from the worktree with
`/proc/<pid>/cwd` checked, anon for both pages, and signed in for
`/settings`. That covers acceptance 4, since the link is a plain
`/settings`.

**W-035 (follow-up):** the link is not the problem. What it leads to
is. A signed-out reader of the terms or privacy page who clicks it gets
`{"detail":"not authenticated"}`. W-022 put the first such link on a
public page, and my W-022 review missed it. That change is outside
W-034's scope.

The developer appended an entry to `docs/IDEAS.md`, which is Paulo's
inbox. Drive-bys belong in `DEV_NOTES.md`. The entry says it was Paulo's
call, so it is left there.

**Merge order:** W-025 still claims 1.9.14, which W-022 has taken. It
renumbers when it merges, and must skip 1.9.15 if this has landed. If
this merges after 23 October, both dates move to the merge day (TODO
says so).

**Not verified:**
- The rendered pages in a browser. The developer checked the HTML,
  not the look. The footnote reuses an existing class.
- What a signed-out click shows: it is W-035's subject, and known to
  be the raw 401.
