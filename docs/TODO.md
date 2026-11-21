# TODO: #33 — /bot, the page the scraper's user agent names, is a 404

> The developer's per-ticket checklist, overwritten by the next ticket.

_2026-11-20_

- [x] `CRAWLER_NAME: str | None = None` in `Settings`
- [x] `GET`/`HEAD /bot` → `bot.html` in the site layout, anon and signed in
- [x] Four facts, checked against scraper `src/crawl_policy.py` at 0.100.0: who, what it collects, what it obeys, how to opt out (`crawler@indierunners.co`)
- [x] Name unset: 200, no crawler named, no placeholder; robots example says to use the name in the user agent
- [x] `/bot` in `sitemap.xml`; not disallowed by `robots.txt`
- [x] No link to `docs/CRAWLING.md`: it does not exist in the scraper (checked 2026-11-20), and that repo is private
- Measure: page text both ways (name set / unset), both tiers; sitemap and robots bodies.
- Disproved: that the policy module covers every request (#73 R1). The hand-run add/move one-page check skips robots.txt; the page claims robots.txt for crawls only.
