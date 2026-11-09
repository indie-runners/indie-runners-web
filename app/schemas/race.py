from datetime import date
from typing import Optional, Any

from pydantic import BaseModel


class EventListItem(BaseModel):
    event_id: str
    event_slug: Optional[str]
    occurrence_year: Optional[str]
    occurrence_id: Optional[int] = None
    name: str
    location: Optional[str]
    country: Optional[str]
    race_date: Optional[date]
    race_date_end: Optional[date] = None
    race_date_display: Optional[str] = None
    is_tbc: bool = False
    expected_month: Optional[int] = None
    expected_year: Optional[int] = None
    distances: list[float]
    terrain_type: Optional[str]
    race_status: Optional[str]
    registration_open: Optional[bool] = None  # True if any race is open; None is unknown, not closed
    price: Optional[float]  # lowest price across the event's races; under mixed currency, the earliest-dated one, not a floor
    price_max: Optional[float] = None  # set only when the races differ in price
    price_currency: Optional[str]
    gradient_class: str
    going_count: int = 0
    interested_count: int = 0
    going_users: list[Any] = []
    interested_users: list[Any] = []
    going_hidden_count: int = 0
    interested_hidden_count: int = 0
    user_status: Optional[str] = None  # current user's status for this race
    attendance_locked: bool = False  # last known day has passed: no mark, no remove (W-072)
    tile_image_url: Optional[str] = None

    class Config:
        from_attributes = True


# kept for backwards compat — alias
RaceListItem = EventListItem
