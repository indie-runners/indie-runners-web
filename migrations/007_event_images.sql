-- 007_event_images.sql
-- Creates web.event_images, a soft reference table marking which events have a
-- dedicated hand picked tile image. The presence of a row is the flag; there
-- is no boolean column. source and attribution exist as a provenance record
-- for licensing purposes even if never displayed on the site.
--
-- event_id and event_slug are soft references to core.events. No FK
-- constraint, same pattern as web.attendance.

CREATE TABLE web.event_images (
    id          SERIAL PRIMARY KEY,
    event_id    INTEGER NOT NULL,
    event_slug  VARCHAR(255) NOT NULL,
    source      VARCHAR(50),
    attribution VARCHAR(255),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (event_id)
);

CREATE INDEX idx_event_images_event_slug ON web.event_images (event_slug);
