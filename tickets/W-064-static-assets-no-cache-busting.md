# W-064 — Static assets carry no cache policy and no version, so a deploy can pair new HTML with old CSS

`priority: 5` · `effort: S` · `area: templates` · `deploy: batched`
`source: W-028 review, 2026-10-27`

## What is wrong

`base.html:10` and `:83` load `/static/css/main.css` and
`/static/js/attendance.js` with no version in the URL, and `StaticFiles`
(`app/main.py:89`) sends no `Cache-Control`. Production, 2026-10-27:

```
$ curl -sI https://indierunners.co/static/css/main.css
HTTP/2 200
last-modified: Mon, 26 Oct 2026 21:19:48 GMT
etag: "e673b346d656887edce56d6236be142c"
```

Browsers then cache heuristically (typically 10% of the time since
`last-modified`) without revalidating. For a while after a deploy, a
returning visitor can get the new HTML with the old stylesheet. Every
CSS change has shipped this way. W-028 is the first where it shows: its
new `avatar--anon-N` classes have no rules in the old CSS, so the
circles would render with no background.

Not observed in production. This is the mechanism, not a sighting.

## Acceptance

1. After a deploy, a browser that cached the previous `main.css` fetches
   the new one on its next page load. Say how this was shown.
2. Every `/static/` reference in the templates gets the same treatment,
   not just these two.
3. Changelog names the mechanism chosen and why.

## Out of scope

A CDN or asset pipeline. The brand pack under `static/brand/`.

## Verdict

**VERDICT: APPROVED WITH FOLLOW-UPS — W-075** — 2026-10-30. Folded into
W-074 (`fix/gcal-popup-silent`, 1.9.48) on Paulo's word, after W-074's
cause turned out to be this ticket's mechanism. The review is in
`tickets/W-074-gcal-popup-silent-on-production.md`.
