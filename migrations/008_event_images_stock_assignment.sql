-- 008_event_images_stock_assignment.sql
-- Extends web.event_images to persist stock-tile assignments.
--
-- Before: presence of a row = dedicated tile flag. Only dedicated rows
-- were ever inserted.
-- After:  every event gets a row. `kind` distinguishes 'dedicated' (hand
-- picked photo) from 'stock' (random terrain-matched slot from
-- app/imaging/stock_manifest.json). `stock_filename` stores the manifest
-- filename for stock rows. `terrain` records the bucket used at
-- assignment time (auditing, future reassignment).
--
-- Prerequisite: SELECT COUNT(*) FROM web.event_images must return 0.
-- Verified 2026-07-10. Otherwise the CHECK constraint on
-- (kind='dedicated' OR stock_filename IS NOT NULL) fails at ADD time,
-- since existing rows would default to kind='stock' with NULL filename.
-- If ever non-empty in the future, split into: add columns → backfill
-- kind/stock_filename per row → add constraints.

ALTER TABLE web.event_images
    ADD COLUMN kind           VARCHAR(20)  NOT NULL DEFAULT 'stock',
    ADD COLUMN stock_filename VARCHAR(255),
    ADD COLUMN terrain        VARCHAR(20);

ALTER TABLE web.event_images
    ADD CONSTRAINT ck_event_images_kind
        CHECK (kind IN ('dedicated', 'stock'));

ALTER TABLE web.event_images
    ADD CONSTRAINT ck_event_images_stock_has_filename
        CHECK (kind = 'dedicated' OR stock_filename IS NOT NULL);
