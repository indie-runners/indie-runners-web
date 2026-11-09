-- 005_attendance_race_date.sql
-- Additive. Adds race_date and event_display_name snapshots to web.attendance
-- so the profile page can split going events into upcoming and past without
-- touching core.mv_denormalized_event_data.
--
-- Take a manual Cloud SQL backup before running on production.
-- Run each step separately. Verify counts before proceeding.

-- Step 1: add columns
ALTER TABLE web.attendance ADD COLUMN race_date DATE;
ALTER TABLE web.attendance ADD COLUMN event_display_name VARCHAR(255);

-- Step 2a: backfill race_date from the MV.
-- MAX(occurrence_start_date) per event so the event stays in Going
-- until its last race has passed.
-- Rows with no match (event no longer in the MV) stay NULL and read as Past.
UPDATE web.attendance a
SET race_date = sub.max_date
FROM (
    SELECT event_id, MAX(occurrence_start_date::date) AS max_date
    FROM core.mv_denormalized_event_data
    GROUP BY event_id
) sub
WHERE a.event_id = sub.event_id::bigint
  AND a.race_date IS NULL;

-- Step 2b: backfill event_display_name from the MV.
UPDATE web.attendance a
SET event_display_name = sub.name
FROM (
    SELECT DISTINCT ON (event_id) event_id, event_display_name AS name
    FROM core.mv_denormalized_event_data
    ORDER BY event_id
) sub
WHERE a.event_id = sub.event_id::bigint
  AND a.event_display_name IS NULL;

-- Step 3: verification.
-- Rows still missing race_date have no matching upcoming occurrence.
-- Confirm this count is expected before considering the migration done.
SELECT count(*) AS rows_without_date FROM web.attendance WHERE race_date IS NULL;
