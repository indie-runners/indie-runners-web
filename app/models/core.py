# READ ONLY — maps to core.v_denormalized_event_data_upcoming, owned by indie-runners-scraper
# Do not write to this table or any other core.* table from this service.

from datetime import date, datetime, time

from sqlalchemy import Text, Double, Date, DateTime, Time, Boolean, Integer, MetaData, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class CoreBase(DeclarativeBase):
    metadata = MetaData(schema="core")


class Race(CoreBase):
    __tablename__ = "v_denormalized_event_data_upcoming"

    # `uuid` in the view, so it must be declared as one: mapping it as Text
    # made every load-by-PK emit `WHERE mv_id = $1::VARCHAR`, which Postgres
    # rejects outright (`operator does not exist: uuid = character varying`).
    # That fires whenever a Race is expired and re-accessed — which is what a
    # commit on the request's session does to every object it has loaded.
    # `as_uuid=False` keeps the Python-side value a plain string; the rest of
    # the app assumes `str` and nothing here is worth widening to UUID objects.
    mv_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    race_id: Mapped[str] = mapped_column(Text)
    event_id: Mapped[str] = mapped_column(Text)
    event_name: Mapped[str | None] = mapped_column(Text)
    event_display_name: Mapped[str | None] = mapped_column(Text)
    event_slug: Mapped[str | None] = mapped_column(Text)
    event_website_url: Mapped[str | None] = mapped_column(Text)
    event_location: Mapped[str | None] = mapped_column(Text)
    event_country_code: Mapped[str | None] = mapped_column(Text)
    event_country_alpha2: Mapped[str | None] = mapped_column(Text)
    event_type: Mapped[str | None] = mapped_column(Text)
    race_name: Mapped[str | None] = mapped_column(Text)
    race_slug: Mapped[str | None] = mapped_column(Text)
    race_display_name: Mapped[str | None] = mapped_column(Text)
    race_sort_order: Mapped[str | None] = mapped_column(Text)
    race_distance: Mapped[float | None] = mapped_column(Double)
    race_distance_label: Mapped[str | None] = mapped_column(Text)
    race_date: Mapped[date | None] = mapped_column(Date)
    terrain_type: Mapped[str | None] = mapped_column(Text)
    # JSON array serialised as text, e.g. '["relay", "timed"]'. A race can
    # carry more than one format. Parse via race_service.parse_race_formats.
    race_format: Mapped[str | None] = mapped_column(Text)
    # Event-level prose, not race-level: every race row of a given event
    # carries the same value (verified — no event holds two distinct ones).
    short_description: Mapped[str | None] = mapped_column(Text)
    race_status: Mapped[str | None] = mapped_column(Text)
    registration_price: Mapped[float | None] = mapped_column(Double)
    price_currency: Mapped[str | None] = mapped_column(Text)
    race_location: Mapped[str | None] = mapped_column(Text)
    # text in the view, like every occurrence_* column (W-014). Declared Integer,
    # it came back as a str anyway; readers int() it.
    occurrence_id: Mapped[str | None] = mapped_column(Text)
    occurrence_year: Mapped[str | None] = mapped_column(Text)
    occurrence_start_date: Mapped[str | None] = mapped_column(Text)
    occurrence_end_date: Mapped[str | None] = mapped_column(Text)
    occurrence_status: Mapped[str | None] = mapped_column(Text)
    # MV projects this as text (same pattern as occurrence_year). Cast to
    # int at query time when used in make_date / COALESCE arithmetic.
    occurrence_expected_month: Mapped[str | None] = mapped_column(Text)
    # timestamptz in the view, unlike its neighbour event_last_scraped_at,
    # which is text. Event-level: every row of an event carries the same value.
    event_last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Answer columns — race-specific (race_specific = 1)
    cumulative_ascent: Mapped[float | None] = mapped_column(Double)
    registration_start: Mapped[date | None] = mapped_column(Date)
    registration_open: Mapped[bool | None] = mapped_column(Boolean)
    registration_sold_out: Mapped[bool | None] = mapped_column(Boolean)
    cutoff_time: Mapped[float | None] = mapped_column(Double)
    gpx_available: Mapped[bool | None] = mapped_column(Boolean)
    lottery_system: Mapped[bool | None] = mapped_column(Boolean)
    aid_stations_count: Mapped[int | None] = mapped_column(Integer)
    start_time: Mapped[time | None] = mapped_column(Time)
    mandatory_gear: Mapped[bool | None] = mapped_column(Boolean)
    bag_storage: Mapped[bool | None] = mapped_column(Boolean)
    # Answer columns — shared/event-wide (race_specific = 0)
    qualification_required: Mapped[bool | None] = mapped_column(Boolean)
    early_bird_discounts: Mapped[bool | None] = mapped_column(Boolean)
    registration_transferable: Mapped[bool | None] = mapped_column(Boolean)
    registration_refundable: Mapped[bool | None] = mapped_column(Boolean)
    registration_postponable: Mapped[bool | None] = mapped_column(Boolean)
    national_league: Mapped[str | None] = mapped_column(Text)
    additional_fees: Mapped[bool | None] = mapped_column(Boolean)
    pacers_allowed: Mapped[bool | None] = mapped_column(Boolean)
    finisher_apparel: Mapped[bool | None] = mapped_column(Boolean)
    accommodation_recommendations: Mapped[bool | None] = mapped_column(Boolean)
    live_tracking: Mapped[bool | None] = mapped_column(Boolean)
    finisher_medal: Mapped[bool | None] = mapped_column(Boolean)
