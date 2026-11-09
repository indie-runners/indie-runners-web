# indie-runners-web

The web service behind [indierunners.co](https://indierunners.co): FastAPI and server-rendered Jinja templates.

## How this repo is built

Since 2026-08-28, the work has run as four roles: auditor, PM, developer and chief of staff. Each role is a Claude Code session opened with a brief under `docs/roles/` ([start here](docs/roles/README.md)). Paulo sets direction and priorities and makes every production decision. Under those briefs, the sessions write most of the code and every ticket, review and changelog entry. Commits carry the session's model as co-author.

## License

Copyright (C) 2026 Paulo Morales Castillo

Licensed under the GNU Affero General Public License v3.0; see [LICENSE](LICENSE).

The Instagram, Strava and GitHub marks in `static/icons/` (`instagram.svg`, `strava.svg`, `github.svg`) belong to their owners and are not under this license. `static/maps/europe.json` is cropped from MapSVG's world map, licensed CC BY 4.0.

The GCP project, Cloud SQL instance, bucket and service account names in this repo are public on purpose; access is controlled by IAM.
