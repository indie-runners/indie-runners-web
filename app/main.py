import hashlib
import json
import logging
import math
from collections import Counter
from functools import lru_cache
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote, urlparse
from xml.sax.saxutils import escape

from fastapi import FastAPI, Depends, Form, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, select, text

from app.config import settings
from app.db import get_db
from app.models.web import User
from app.models.core import Race
from app.services.auth_service import CodeExchangeRefused, GoogleAuthService
from app.services.user_service import UserService
from app.services.race_service import (
    event_location,
    RACE_FORMAT_CHOICES,
    RACE_FORMAT_SLUGS,
    RaceService,
    RaceFilters,
    format_tbc_expected,
    gcal_url,
    race_format_labels,
    truncate_for_meta,
)
from app.services.attendance_service import AttendanceService, is_locked
from app.services.crew_service import CrewService
from app.services.profile_service import ProfileService
from app.services.settings_service import SettingsService
from app.services.event_image_service import EventImageService
from app.imaging.dedicated_index import load_dedicated_slugs
from app.imaging.resolver import resolve_tile_image

logger = logging.getLogger(__name__)

app = FastAPI(title="Indie Runners Web")


@app.on_event("startup")
def _load_dedicated_slugs() -> None:
    app.state.dedicated_slugs = load_dedicated_slugs()
    logger.info(f"Loaded {len(app.state.dedicated_slugs)} dedicated event slugs")

    from app.db import SessionLocal
    db = SessionLocal()
    try:
        updated = EventImageService(db).refresh_dedicated_attributions(
            app.state.dedicated_slugs
        )
        if updated:
            logger.info(f"Refreshed dedicated attributions on {updated} rows")
    finally:
        db.close()

_CANONICAL_HOST = "indierunners.co"
_REDIRECTED_HOSTS = {"beta.indierunners.co", "www.indierunners.co"}


class CanonicalDomainMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.hostname in _REDIRECTED_HOSTS:
            return RedirectResponse(
                url=str(request.url.replace(hostname=_CANONICAL_HOST)),
                status_code=301,
            )
        return await call_next(request)


class SameOriginMiddleware(BaseHTTPMiddleware):
    """Refuse a state-changing request whose Origin host is not this host (W-031).

    SameSite=lax still sends the session cookie from a sibling subdomain (same
    site), so every non-safe method checks the request came from this host.
    A browser attaches Origin to every POST/DELETE, form or fetch, so a missing
    Origin cannot come from a sibling page: it passes, which also keeps the
    curl recipe in the developer brief working. ``Origin: null`` has no host
    and is refused. That holds only while no page sets a document-level
    ``no-referrer`` policy (meta tag or Referrer-Policy header): under one, a
    form submit sends ``Origin: null`` and every form here would 403, and the
    event page's back link loses the filters it reads from Referer (W-102).
    """

    async def dispatch(self, request, call_next):
        origin = request.headers.get("origin")
        if (
            request.method not in ("GET", "HEAD", "OPTIONS")
            and origin is not None
            and urlparse(origin).netloc != request.headers.get("host")
        ):
            return PlainTextResponse("cross-origin request refused", status_code=403)
        return await call_next(request)


class StaticCacheMiddleware(BaseHTTPMiddleware):
    """Without a policy browsers kept /static for days unasked (W-074: a stale attendance.js).

    A versioned URL (static_url) never changes content, so it may be cached for a year;
    anything else must be revalidated on every load.
    """

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            versioned = "v" in request.query_params
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable" if versioned else "no-cache"
        return response


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="session",
    https_only=not settings.debug,
    same_site="lax",
)
app.add_middleware(SameOriginMiddleware)
app.add_middleware(StaticCacheMiddleware)
app.add_middleware(CanonicalDomainMiddleware)

_static_dir = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Europe crop of @svg-maps/world 2.0.0 (CC BY 4.0, MapSVG), simplified to {alpha2: path}.
# shortcut: generator not kept (recipe in DEV_NOTES), re-crop if events leave Europe.
_europe_map = json.loads((_static_dir / "maps" / "europe.json").read_text())


def _trimnum(value) -> str:
    """Render a filter value the way the user typed it.

    Query params are coerced to float, so a submitted `12` comes back as
    `12.0` and reappears in the input box that way. Drop the trailing `.0`
    for whole numbers while preserving genuine fractions like `1.5`.
    """
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


templates.env.filters["trimnum"] = _trimnum
templates.env.globals["gcal_url"] = gcal_url


@lru_cache
def static_url(path: str) -> str:
    """/static URL carrying the file's content hash, so a changed file is a new URL (W-074)."""
    # shortcut: hashed once per process; right on Cloud Run (new process per image), and a
    # local static edit needs a uvicorn restart (--reload watches .py only). Upgrade if that bites.
    digest = hashlib.md5((_static_dir / path).read_bytes()).hexdigest()[:8]
    return f"/static/{path}?v={digest}"


templates.env.globals["static_url"] = static_url


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    return db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()


def get_required_user(user: Optional[User] = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="not authenticated")
    return user


def _signin_url(request: Request) -> str:
    # Back to this exact URL after sign-in, query string kept (W-085).
    target = request.url.path + (f"?{request.url.query}" if request.url.query else "")
    return f"/auth/google?next={quote(target, safe='/')}"


def _parse_filters(
    distance_min: Optional[str] = None,
    distance_max: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
    formats: Optional[list[str]] = None,
    cutoff_min: Optional[str] = None,
    cutoff_max: Optional[str] = None,
) -> RaceFilters:
    def _float(v):
        try:
            return float(v) if v else None
        except (ValueError, TypeError):
            return None

    def _date(v):
        try:
            return date.fromisoformat(v) if v else None
        except (ValueError, TypeError):
            return None

    # Whitelisted against the known slugs so a junk ?format=zzz cannot mark
    # the filter set active, auto-open the advanced panel, or reach the query.
    clean_formats = [f for f in (formats or []) if f in RACE_FORMAT_SLUGS]

    return RaceFilters(
        distance_min=_float(distance_min),
        distance_max=_float(distance_max),
        date_from=_date(date_from),
        date_to=_date(date_to),
        country=country or None,
        search=search.strip() if search and search.strip() else None,
        formats=clean_formats,
        cutoff_min=_float(cutoff_min),
        cutoff_max=_float(cutoff_max),
    )


@app.api_route("/", methods=["GET", "HEAD"])
def index(
    request: Request,
    distance_min: Optional[str] = None,
    distance_max: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
    # Repeatable: ?format=relay&format=timed. Needs Query(alias=...) — a bare
    # str param would silently keep only one of the submitted checkboxes.
    formats: list[str] = Query(default=[], alias="format"),
    cutoff_min: Optional[str] = None,
    cutoff_max: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    filters = _parse_filters(
        distance_min, distance_max, date_from, date_to, country, search, formats,
        cutoff_min, cutoff_max,
    )
    race_svc = RaceService(db)
    races = race_svc.list_races(filters)
    countries = race_svc.country_list()

    # Tile images: lazy-on-read assignment, one dict lookup per race
    image_events = [
        {"event_id": r.event_id, "event_slug": r.event_slug, "terrain_type": r.terrain_type}
        for r in races if r.event_id is not None
    ]
    dedicated_slugs = request.app.state.dedicated_slugs
    images = EventImageService(db).get_or_create_for_events(
        image_events, dedicated_slugs=dedicated_slugs
    )
    for race in races:
        if race.event_id is not None:
            row = images.get(int(race.event_id))
            if row is not None and race.event_slug is not None:
                race.tile_image_url = resolve_tile_image(
                    race.event_slug, row, dedicated_slugs
                )

    # Attendance: two queries max (summary + user), no per-tile queries
    occurrence_ids = [r.occurrence_id for r in races if r.occurrence_id is not None]
    att_svc = AttendanceService(db)
    viewer_crews = CrewService(db).get_viewer_crew_ids(current_user.id if current_user else None)
    summaries = att_svc.get_attendance_summary(
        occurrence_ids,
        viewer_user_id=current_user.id if current_user else None,
        viewer_crews=viewer_crews,
    )
    user_attendance = (
        att_svc.get_attendance_for_user(current_user.id, occurrence_ids) if current_user else {}
    )

    for race in races:
        if race.occurrence_id is not None:
            oid = race.occurrence_id
            summary = summaries.get(oid)
            if summary:
                race.going_count = summary.going_count
                race.interested_count = summary.interested_count
                race.going_users = [
                    {"id": u.id, "display_name": u.display_name, "avatar_url": u.avatar_url}
                    for u in summary.going_users
                ]
                race.interested_users = [
                    {"id": u.id, "display_name": u.display_name, "avatar_url": u.avatar_url}
                    for u in summary.interested_users
                ]
                race.going_hidden_count = summary.going_hidden_count
                race.interested_hidden_count = summary.interested_hidden_count
            race.user_status = user_attendance.get(oid)

    def _sort_date(r):
        if r.is_tbc:
            if r.expected_year is None:
                return date.max
            return date(r.expected_year, r.expected_month or 12, 1)
        return r.race_date or date.max

    races.sort(key=lambda r: (-r.going_count, -r.interested_count, _sort_date(r)))
    total_races = len(races)
    races = races[:60]

    # Keyed only on the advanced fields, so the panel does not spring open for
    # a plain country or date filter — but does stay open on a shared URL that
    # carries an advanced one, which would otherwise look like lost filters.
    has_advanced_filters = any([
        filters.formats,
        filters.cutoff_min is not None,
        filters.cutoff_max is not None,
    ])

    has_active_filters = any([
        filters.distance_min is not None,
        filters.distance_max is not None,
        filters.date_from is not None,
        filters.date_to is not None,
        filters.country,
        filters.search,
        has_advanced_filters,
    ])

    if current_user:
        logger.info(f"Rendering index page for user {current_user.id}")

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "races": races,
            "total_races": total_races,
            "filters": filters,
            "countries": countries,
            "current_user": current_user,
            "has_active_filters": has_active_filters,
            "has_advanced_filters": has_advanced_filters,
            "race_format_choices": RACE_FORMAT_CHOICES,
        },
    )


def _attendance_response(att_svc: AttendanceService, occurrence_id: int, current_user: User, db: Session) -> dict:
    viewer_crews = CrewService(db).get_viewer_crew_ids(current_user.id)
    summaries = att_svc.get_attendance_summary(
        [occurrence_id], viewer_user_id=current_user.id, viewer_crews=viewer_crews,
    )
    user_att = att_svc.get_attendance_for_user(current_user.id, [occurrence_id])
    summary = summaries.get(occurrence_id)
    return {
        "going_count": summary.going_count if summary else 0,
        "interested_count": summary.interested_count if summary else 0,
        "user_status": user_att.get(occurrence_id),
        "going_users": [
            {"id": u.id, "display_name": u.display_name, "avatar_url": u.avatar_url}
            for u in (summary.going_users if summary else [])
        ],
        "interested_users": [
            {"id": u.id, "display_name": u.display_name, "avatar_url": u.avatar_url}
            for u in (summary.interested_users if summary else [])
        ],
        "going_hidden_count": summary.going_hidden_count if summary else 0,
        "interested_hidden_count": summary.interested_hidden_count if summary else 0,
    }


@app.post("/events/{event_id}/{occurrence_id}/attendance")
def mark_attendance(
    event_id: int,
    occurrence_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    att_svc = AttendanceService(db)
    try:
        att_svc.mark_attendance(current_user.id, event_id, occurrence_id, status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _attendance_response(att_svc, occurrence_id, current_user, db)


@app.delete("/events/{event_id}/{occurrence_id}/attendance")
def clear_attendance(
    event_id: int,
    occurrence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    att_svc = AttendanceService(db)
    try:
        att_svc.clear_attendance(current_user.id, occurrence_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _attendance_response(att_svc, occurrence_id, current_user, db)


@app.api_route("/events/{event_slug}/{occurrence_year}", methods=["GET", "HEAD"])
def event_detail(
    request: Request,
    event_slug: str,
    occurrence_year: str,
    race: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    # str, not int: a malformed year (2027x) gets the not-found page, not FastAPI's JSON 422 (#14).
    if not (occurrence_year.isascii() and occurrence_year.isdigit()):
        return templates.TemplateResponse(
            request, "event_not_found.html", {"current_user": current_user}, status_code=404
        )
    occurrence_year = int(occurrence_year)
    # ProfileService._load_rows mirrors this predicate (has_page) to decide what to link; change both.
    rows = db.execute(
        select(Race)
        .where(Race.event_slug == event_slug)
        .where(Race.occurrence_year == str(occurrence_year))
        .order_by(Race.race_distance.desc().nulls_last())
    ).scalars().all()

    if not rows:
        # A finished edition leaves the view the day after it runs; send old links on.
        years = sorted(int(y) for y in db.execute(
            select(Race.occurrence_year).where(Race.event_slug == event_slug).distinct()
        ).scalars() if y and y.isdigit())
        if years:
            target = next((y for y in years if y > occurrence_year), years[-1])
            # 302: the target moves every year, and D+2 retention can bring the old year back.
            return RedirectResponse(f"/events/{event_slug}/{target}", status_code=302)
        return templates.TemplateResponse(
            request, "event_not_found.html", {"current_user": current_user}, status_code=404
        )

    selected = next((r for r in rows if r.race_slug == race), rows[0])

    # Back to the filtered index the runner came from (W-102). Only the query is taken, behind a
    # literal "/?", so the link cannot leave this site's index.
    # shortcut: survives one hop (a race pick in the table reloads to "/"), upgrade if the table stops being a full navigation.
    ref = urlparse(request.headers.get("referer", ""))
    same_index = ref.netloc == request.headers.get("host") and ref.path == "/" and ref.query
    back_href = f"/?{ref.query}" if same_index else "/"

    def _fmt_date(raw: str | None) -> str | None:
        if not raw:
            return None
        try:
            from datetime import date as _date
            return _date.fromisoformat(raw).strftime("%-d %B")
        except (ValueError, TypeError):
            return raw

    first = rows[0]
    location = event_location(rows)
    is_tbc = first.occurrence_status == "tbc"
    race_dates = [r.race_date for r in rows if r.race_date is not None]
    try:
        expected_year = int(first.occurrence_year) if first.occurrence_year else None
    except (TypeError, ValueError):
        expected_year = None
    try:
        expected_month = int(first.occurrence_expected_month) if first.occurrence_expected_month else None
    except (TypeError, ValueError):
        expected_month = None
    tbc_display = format_tbc_expected(expected_year, expected_month) if is_tbc else None

    event = {
        "event_id": int(first.event_id) if first.event_id and first.event_id.isdigit() else None,
        "occurrence_id": int(first.occurrence_id) if first.occurrence_id is not None else None,
        "event_slug": first.event_slug,
        "event_display_name": first.event_display_name or first.event_name,
        "event_location": location,
        "event_country_code": first.event_country_code,
        "event_type": first.event_type,
        "event_website_url": first.event_website_url,
        "occurrence_year": first.occurrence_year,
        "occurrence_start_date": _fmt_date(first.occurrence_start_date),
        # A same-day end is dropped so the hero prints one date (W-047); compared raw, year included.
        "occurrence_end_date": (_fmt_date(first.occurrence_end_date)
                                if first.occurrence_end_date != first.occurrence_start_date else None),
        "is_tbc": is_tbc,
        "expected_year": expected_year,
        "expected_month": expected_month,
        "tbc_display": tbc_display,
        # From the races, as the tile: occurrence_end_date can stop before the last race.
        "gcal_url": None if is_tbc or not race_dates else gcal_url(
            first.event_display_name or first.event_name or "",
            min(race_dates), max(race_dates), location,
        ),
        # Event-level: identical on every race row of this occurrence.
        "short_description": first.short_description,
    }

    # Shown to anonymous visitors and used as the page's meta description —
    # this field is part of the SEO surface, so it sits outside the sign-in gate.
    meta_description = truncate_for_meta(first.short_description)

    tile_image_url = None
    tile_attribution_name = None
    tile_attribution_url = None
    tile_attribution_source_url = None
    if event["event_id"] is not None:
        logger.info("resolving hero image for event page")
        # `first` is one race row and may have a NULL terrain while a sibling
        # race carries a real one, so take the first non-NULL across the event.
        # Only matters when the event's races agree; conflicting terrain across
        # races is a known data-shape limit of one image per event.
        event_terrain = next(
            (r.terrain_type for r in rows if r.terrain_type is not None), None
        )
        image_events = [{
            "event_id": event["event_id"],
            "event_slug": event["event_slug"],
            "terrain_type": event_terrain,
        }]
        images = EventImageService(db).get_or_create_for_events(
            image_events, dedicated_slugs=request.app.state.dedicated_slugs
        )
        img = images.get(event["event_id"])
        if img is not None and event["event_slug"]:
            tile_image_url = resolve_tile_image(
                event["event_slug"], img, request.app.state.dedicated_slugs,
            )
            tile_attribution_name = img.attribution_name
            tile_attribution_url = img.attribution_url
            tile_attribution_source_url = img.attribution_source_url

    occurrence_id = event["occurrence_id"]
    att_svc = AttendanceService(db)
    if occurrence_id is not None:
        viewer_crews = CrewService(db).get_viewer_crew_ids(current_user.id if current_user else None)
        summaries = att_svc.get_attendance_summary(
            [occurrence_id],
            viewer_user_id=current_user.id if current_user else None,
            viewer_crews=viewer_crews,
        )
        user_attendance = (
            att_svc.get_attendance_for_user(current_user.id, [occurrence_id]) if current_user else {}
        )
        summary = summaries.get(occurrence_id)
    else:
        summary = None
        user_attendance = {}

    attendance_summary = {
        "going_count": summary.going_count if summary else 0,
        "interested_count": summary.interested_count if summary else 0,
        "going_users": [
            {"id": u.id, "display_name": u.display_name, "avatar_url": u.avatar_url}
            for u in (summary.going_users if summary else [])
        ],
        "interested_users": [
            {"id": u.id, "display_name": u.display_name, "avatar_url": u.avatar_url}
            for u in (summary.interested_users if summary else [])
        ],
        "going_hidden_count": summary.going_hidden_count if summary else 0,
        "interested_hidden_count": summary.interested_hidden_count if summary else 0,
    }
    user_status = user_attendance.get(occurrence_id) if occurrence_id else None
    attendance_locked = is_locked(first.occurrence_start_date, first.occurrence_end_date)

    # race_format is a JSON array string on the MV; parse once per row here
    # rather than in the template. Keyed by race_slug, which is unique
    # within an (event_slug, occurrence_year) pair.
    race_formats = {
        r.race_slug: race_format_labels(r.race_format)
        for r in rows
        if r.race_slug is not None
    }
    any_race_formats = any(race_formats.values())

    logger.info(f"Event detail page for {event_slug} {occurrence_year}")

    return templates.TemplateResponse(
        request,
        "event.html",
        {
            "event": event,
            "races": rows,
            "selected_race": selected,
            "back_href": back_href,
            "race_formats": race_formats,
            "any_race_formats": any_race_formats,
            "meta_description": meta_description,
            "current_user": current_user,
            "attendance_summary": attendance_summary,
            "user_status": user_status,
            "attendance_locked": attendance_locked,
            "occurrence_id": occurrence_id,
            "tile_image_url": tile_image_url,
            "tile_attribution_name": tile_attribution_name,
            "tile_attribution_url": tile_attribution_url,
            "tile_attribution_source_url": tile_attribution_source_url,
        },
    )


@app.api_route("/profile", methods=["GET", "HEAD"])
def profile_self(request: Request, current_user: Optional[User] = Depends(get_current_user)):
    if current_user is None:
        return RedirectResponse(_signin_url(request), status_code=303)
    return RedirectResponse(f"/profile/{current_user.id}")


@app.api_route("/profile/{user_id}", methods=["GET", "HEAD"])
def profile(
    request: Request,
    user_id: str,
    preview: Optional[str] = None,
    left: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    # str, not int: a malformed id (27+) gets the unknown-id placeholder, not FastAPI's JSON 422 (#14).
    if not (user_id.isascii() and user_id.isdigit()):
        return templates.TemplateResponse(
            request, "profile_hidden.html", {"current_user": current_user, "preview_mode": False}
        )
    user_id = int(user_id)
    viewer_id = current_user.id if current_user else None
    # Preview mode: when the user is looking at their own profile via
    # the settings "View as others see it" link, drop the self
    # short-circuit so they see exactly what a signed-in stranger would.
    preview_mode = preview == "1" and viewer_id is not None and viewer_id == user_id
    effective_viewer = None if preview_mode else viewer_id
    if preview_mode:
        # Anon-style probe would hide public profiles too (BRIEF PR1
        # baseline). Preview should show what a signed-in stranger sees,
        # so pass a sentinel viewer id that is not the target and not
        # anonymous — any id will do since we only use it to fail the
        # self short-circuit. Preview intentionally passes an empty
        # crews set so a crews_only target renders as it would for a
        # signed-in stranger with no shared crew.
        effective_viewer = -1
    viewer_crews_for_profile = (
        set() if preview_mode else CrewService(db).get_viewer_crew_ids(effective_viewer)
    )
    profile_view = ProfileService(db).get_profile(
        user_id,
        viewer_user_id=effective_viewer,
        viewer_crews=viewer_crews_for_profile,
    )

    if not profile_view.is_visible:
        return templates.TemplateResponse(
            request,
            "profile_hidden.html",
            {"current_user": current_user, "preview_mode": preview_mode},
            status_code=200,
        )

    viewer_is_self = (not preview_mode) and viewer_id is not None and viewer_id == user_id
    return templates.TemplateResponse(
        request,
        "profile.html",
        {
            "current_user": current_user,
            "viewer_is_self": viewer_is_self,
            "crews": CrewService(db).list_crews_for_user(user_id) if viewer_is_self else [],
            "profile": profile_view,
            "target_user": profile_view.target_user,
            "preview_mode": preview_mode,
            "left": left,
        },
    )


def _settings_context(
    db: Session,
    current_user: User,
    *,
    error: Optional[str] = None,
    saved: bool = False,
) -> dict:
    return {
        "current_user": current_user,
        "current_visibility": current_user.visibility,
        "error": error,
        "saved": saved,
    }


@app.api_route("/settings", methods=["GET", "HEAD"])
def settings_page(
    request: Request,
    saved: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    # Public pages (privacy §8, terms §9) link here, so a signed-out
    # reader goes through sign-in and back rather than to a bare 401.
    if current_user is None:
        return RedirectResponse("/auth/google?next=/settings", status_code=303)
    return templates.TemplateResponse(
        request,
        "settings.html",
        _settings_context(db, current_user, saved=(saved == "1")),
    )


@app.post("/settings")
def settings_update(
    request: Request,
    visibility: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    try:
        SettingsService(db).update_visibility(current_user.id, visibility)
    except ValueError as e:
        return templates.TemplateResponse(
            request,
            "settings.html",
            _settings_context(db, current_user, error=str(e)),
            status_code=400,
        )
    return RedirectResponse("/settings?saved=1", status_code=303)


@app.post("/settings/delete-account")
def settings_delete_account(
    request: Request,
    confirm: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    if confirm.strip().lower() != "delete":
        return templates.TemplateResponse(
            request,
            "settings.html",
            _settings_context(db, current_user, error='Type "delete" to confirm account deletion.'),
            status_code=400,
        )
    UserService(db).delete_account(current_user.id)
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.api_route("/crews", methods=["GET", "HEAD"])
def crews_nav(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    if current_user is None:
        return RedirectResponse(_signin_url(request), status_code=303)
    # The nav's Crews link. A redirect rather than a per-crew href in
    # base.html, so no signed-in render pays a crews query (W-078).
    crews = CrewService(db).list_crews_for_user(current_user.id)
    if len(crews) == 1:
        return RedirectResponse(f"/crews/{crews[0][0].slug}", status_code=303)
    return RedirectResponse(f"/profile/{current_user.id}#crews", status_code=303)


@app.api_route("/crews/new", methods=["GET", "HEAD"])
def crews_new_form(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
):
    if current_user is None:
        return RedirectResponse(_signin_url(request), status_code=303)
    return templates.TemplateResponse(
        request,
        "crews_new.html",
        {"current_user": current_user, "error": None, "display_name": ""},
    )


@app.post("/crews/new")
def crews_new_submit(
    request: Request,
    display_name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    try:
        crew = CrewService(db).create_crew(current_user.id, display_name)
    except ValueError as e:
        return templates.TemplateResponse(
            request,
            "crews_new.html",
            {
                "current_user": current_user,
                "error": str(e),
                "display_name": display_name,
            },
            status_code=400,
        )
    return RedirectResponse(f"/crews/{crew.slug}?created=1", status_code=303)


@app.api_route("/crews/{slug}", methods=["GET", "HEAD"])
def crews_detail(
    request: Request,
    slug: str,
    created: Optional[str] = None,
    rotated: Optional[str] = None,
    joined: Optional[str] = None,
    removed: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    svc = CrewService(db)
    # Anon gets the placeholder before any lookup, so a real and a made-up
    # slug answer the same (W-085). No crew name surfaces without an
    # invite. PLAN Decision 10.
    crew = svc.get_crew_by_slug(slug) if current_user else None
    if crew is None or not svc.is_member(current_user.id, crew.id):
        return templates.TemplateResponse(
            request,
            "crews_hidden.html",
            {"current_user": current_user, "signin_url": _signin_url(request)},
            status_code=200,
        )

    members = svc.list_members(crew.id)
    is_admin = svc.is_admin(current_user.id, crew.id)
    invite = svc.active_invite_for_crew(crew.id)
    invite_url = str(request.url_for("crews_join_form", token=invite.token)) if invite else None
    return templates.TemplateResponse(
        request,
        "crews_detail.html",
        {
            "current_user": current_user,
            "crew": crew,
            "agenda": svc.list_agenda(crew.id, current_user.id),
            "members": members,
            "is_admin": is_admin,
            "invite_url": invite_url,
            "created": created == "1",
            "rotated": rotated == "1",
            "joined": joined == "1",
            "removed": removed == "1",
        },
    )


@app.post("/crews/{slug}/invite/rotate")
def crews_rotate_invite(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    svc = CrewService(db)
    crew = svc.get_crew_by_slug(slug)
    if crew is None or not svc.is_member(current_user.id, crew.id):
        raise HTTPException(status_code=404, detail="Crew not found")
    try:
        svc.rotate_invite(crew.id, current_user.id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return RedirectResponse(f"/crews/{slug}?rotated=1", status_code=303)


@app.post("/crews/{slug}/leave")
def crews_leave(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    # Origin is checked by SameOriginMiddleware (W-031); an only member's leave deletes the crew.
    svc = CrewService(db)
    crew = svc.get_crew_by_slug(slug)
    if crew is None or not svc.is_member(current_user.id, crew.id):
        raise HTTPException(status_code=404, detail="Crew not found")
    name = crew.display_name  # the row may be gone after remove_member
    svc.remove_member(crew.id, current_user.id)
    db.commit()
    logger.info("User %s left crew %s", current_user.id, crew.id)
    return RedirectResponse(f"/profile/{current_user.id}?left={quote(name)}#crews", status_code=303)


@app.post("/crews/{slug}/members/{user_id}/remove")
def crews_remove_member(
    slug: str,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    # Origin is checked by SameOriginMiddleware (W-031). The actor stays, so
    # the crew survives; a removed creator hands over like a leaver (W-082).
    svc = CrewService(db)
    crew = svc.get_crew_by_slug(slug)
    if crew is None or not svc.is_member(current_user.id, crew.id):
        raise HTTPException(status_code=404, detail="Crew not found")
    if not svc.is_admin(current_user.id, crew.id):
        raise HTTPException(status_code=403, detail="Only an admin can remove members")
    if user_id == current_user.id:
        raise HTTPException(status_code=403, detail="Leave the crew instead")
    if not svc.is_member(user_id, crew.id):
        raise HTTPException(status_code=404, detail="Member not found")
    svc.remove_member(crew.id, user_id)
    db.commit()
    logger.info("User %s removed user %s from crew %s", current_user.id, user_id, crew.id)
    return RedirectResponse(f"/crews/{slug}?removed=1", status_code=303)


@app.api_route(
    "/crews/join/{token}", methods=["GET", "HEAD"], name="crews_join_form"
)
def crews_join_form(
    request: Request,
    token: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    # Signed-out visitors get bounced through Google. Stash the target
    # URL so the callback lands them back on this confirm page instead
    # of `/`. The stash is server-set (never from a client query param),
    # so no open-redirect surface.
    if current_user is None:
        request.session["post_login_redirect"] = str(request.url)
        return RedirectResponse("/auth/google", status_code=303)

    crew = CrewService(db).find_crew_by_invite_token(token)
    if crew is None:
        return templates.TemplateResponse(
            request,
            "crews_invite_invalid.html",
            {"current_user": current_user},
            status_code=200,
        )
    return templates.TemplateResponse(
        request,
        "crews_invite_confirm.html",
        {"current_user": current_user, "crew": crew, "token": token},
    )


@app.post("/crews/join/{token}")
def crews_join_accept(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    svc = CrewService(db)
    crew = svc.find_crew_by_invite_token(token)
    if crew is None:
        raise HTTPException(status_code=404, detail="Invite is no longer active")
    svc.add_member(crew.id, current_user.id)
    return RedirectResponse(f"/crews/{crew.slug}?joined=1", status_code=303)


@app.api_route("/imprint", methods=["GET", "HEAD"])
def imprint(request: Request, current_user: Optional[User] = Depends(get_current_user)):
    return templates.TemplateResponse(
        request,
        "imprint.html",
        {"current_user": current_user},
    )


# Browsers request /favicon.ico at the root whatever <head> says.
@app.api_route("/favicon.ico", methods=["GET", "HEAD"])
def favicon():
    return RedirectResponse("/static/brand/favicon/favicon.ico")


# A missing robots.txt reads as "crawl everything"; event pages stay crawlable.
# Not access control: these routes still answer to anyone who asks.
@app.api_route("/robots.txt", methods=["GET", "HEAD"])
def robots():
    return PlainTextResponse(
        "User-agent: *\n"
        "Disallow: /settings\n"
        "Disallow: /profile\n"
        "Disallow: /crews\n"
        "Disallow: /auth/\n"
        f"Sitemap: https://{_CANONICAL_HOST}/sitemap.xml\n"
    )


# Built per request from the index's own query: ~400 rows, the cost /stats
# already pays, and it can never list an event the site has stopped serving.
# Anon-public pages only; nothing robots.txt disallows.
@app.api_route("/sitemap.xml", methods=["GET", "HEAD"])
def sitemap(db: Session = Depends(get_db)):
    paths = ["/", "/stats", "/imprint", "/privacy", "/terms"] + [
        f"/events/{e.event_slug}/{e.occurrence_year}"
        for e in RaceService(db).list_races(RaceFilters())
        if e.event_slug and e.occurrence_year
    ]
    urls = "".join(
        f"<url><loc>{escape(f'https://{_CANONICAL_HOST}{p}')}</loc></url>\n"
        for p in dict.fromkeys(paths)
    )
    return Response(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}</urlset>\n",
        media_type="application/xml",
    )


@app.api_route("/privacy", methods=["GET", "HEAD"])
def privacy(request: Request, current_user: Optional[User] = Depends(get_current_user)):
    return templates.TemplateResponse(
        request,
        "privacy.html",
        {"current_user": current_user},
    )


@app.api_route("/stats", methods=["GET", "HEAD"])
def stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    # Two denominators, never mixed (Paulo, 2026-10-21): the headline counts
    # core.events, stable all year; the rollup and list read the serving view.
    tracked = db.execute(
        text("SELECT count(*) FROM core.events WHERE status = 'active'")
    ).scalar_one()
    since = datetime.now(timezone.utc) - timedelta(days=30)
    checked_30d = db.execute(
        select(func.count(func.distinct(Race.event_id)))
        .where(Race.event_last_checked_at >= since)
    ).scalar_one()
    # Last N with no age filter, so the list is never empty: runs are bursty.
    recent = db.execute(
        select(
            func.max(Race.event_display_name).label("name"),
            func.max(Race.event_slug).label("event_slug"),
            func.max(Race.occurrence_year).label("occurrence_year"),
            func.max(Race.event_last_checked_at).label("checked_at"),
        )
        .where(Race.event_last_checked_at.isnot(None))
        .group_by(Race.event_id)
        .order_by(func.max(Race.event_last_checked_at).desc())
        .limit(10)
    ).all()
    # Counted over list_races, the same query /?country= runs, so every
    # clickable country lands on a non-empty index (the raw view disagrees).
    counts = Counter(e.country for e in RaceService(db).list_races(RaceFilters()))
    counts.pop(None, None)  # no country: not on the map
    alpha2 = dict(db.execute(
        select(Race.event_country_code, func.lower(Race.event_country_alpha2))
        .where(Race.event_country_alpha2.isnot(None))
        .distinct()
    ).all())
    top = max(counts.values(), default=1)
    countries = [
        {"name": c, "alpha2": alpha2.get(c), "n": n,
         "shade": round(0.3 + 0.7 * math.log(n + 1) / math.log(top + 1), 2)}
        for c, n in counts.most_common()
    ]
    return templates.TemplateResponse(
        request,
        "stats.html",
        {
            "current_user": current_user,
            "tracked": tracked,
            "checked_30d": checked_30d,
            "recent": recent,
            "utc": timezone.utc,
            "countries": countries,
            "on_map": {c["alpha2"]: c for c in countries if c["alpha2"]},
            "europe_map": _europe_map,
        },
    )


@app.api_route("/terms", methods=["GET", "HEAD"])
def terms(request: Request, current_user: Optional[User] = Depends(get_current_user)):
    return templates.TemplateResponse(
        request,
        "terms.html",
        {"current_user": current_user},
    )


@app.get("/debug/health")
def health_check(db: Session = Depends(get_db)):
    # Public route: confirms the database answers, and says nothing about its contents.
    db.execute(select(1))
    return {"status": "ok"}


_UNSAFE_NEXT_PREFIXES = ("http:", "https:", "data:", "javascript:")


def _validate_next(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    if raw != raw.strip():
        return None
    if any(c in raw for c in ("\r", "\n", "\t", "\\")):
        return None
    if not raw.startswith("/"):
        return None
    if raw.startswith("//"):
        return None
    lowered = raw.lower()
    if any(lowered.startswith(p) for p in _UNSAFE_NEXT_PREFIXES):
        return None
    return raw


@app.api_route("/auth/google", methods=["GET", "HEAD"])
def google_login(request: Request, next: Optional[str] = None):
    validated = _validate_next(next)
    if next and validated is None:
        logger.info("rejecting unsafe next redirect")
    if validated is not None:
        request.session["post_login_redirect"] = validated
    url = GoogleAuthService().build_authorize_url()
    return RedirectResponse(url)


@app.api_route("/auth/google/callback", methods=["GET", "HEAD"])
async def google_callback(
    request: Request, code: Optional[str] = None, db: Session = Depends(get_db)
):
    # Google sends no `code` when the visitor cancels on the consent screen
    # (error=access_denied). Drop the queued redirect so a later, unrelated
    # sign-in does not land on a stale invite; a signed-in session is untouched.
    if not code:
        request.session.pop("post_login_redirect", None)
        return RedirectResponse("/", status_code=303)
    svc = GoogleAuthService()
    try:
        token_data = await svc.exchange_code_for_token(code)
    except CodeExchangeRefused:
        # A one-time code replayed (reload, back, double tap) after a sign-in
        # that worked: the session is already signed in, so go where it was going.
        if request.session.get("user_id"):
            target = request.session.pop("post_login_redirect", None)
            return RedirectResponse(target or "/", status_code=303)
        # Signed out: say so. The queued redirect stays so Try again still lands there.
        return templates.TemplateResponse(
            request, "signin_failed.html", {"current_user": None}, status_code=400
        )
    userinfo = await svc.get_userinfo(token_data["access_token"])
    try:
        user = UserService(db).get_or_create_user_from_google(userinfo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    request.session["user_id"] = user.id
    # Honour a server-set post-login redirect if one is queued (e.g. an
    # invite-URL landing while signed out). Only routes we control ever
    # set this key, so there is no open-redirect surface.
    target = request.session.pop("post_login_redirect", None)
    return RedirectResponse(target or "/")


@app.api_route("/me", methods=["GET", "HEAD"])
def me(user: User = Depends(get_required_user)):
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
    }


@app.api_route("/auth/logout", methods=["GET", "HEAD"])
def logout(request: Request):
    request.session.clear()
    logger.info("User logged out")
    return RedirectResponse("/")
