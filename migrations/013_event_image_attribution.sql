-- 013_event_image_attribution.sql
-- Adds three nullable attribution columns to web.event_images so the
-- photographer credit rendered in the event page hero can carry a name
-- plus two Unsplash-license-compliant links (photographer profile and
-- photo page).
--
-- Before: web.event_images.attribution (VARCHAR(255), nullable) is the
-- only credit surface. It has never been populated (0 rows) and cannot
-- carry the two URLs the Unsplash credit convention asks for.
-- After:  three new nullable columns mirror the fields already present
-- in app/imaging/stock_manifest.json and (soon) a matching
-- dedicated_manifest.json:
--   attribution_name        — photographer display name
--   attribution_url         — link to the photographer profile
--   attribution_source_url  — link to the photo page (Unsplash)
--
-- The existing `attribution` column is left in place for backward
-- compatibility with the single-string Phase 1 wiring. A follow-up PR
-- can drop it once the three-column form is populated and the template
-- reads only the new fields; that split matches the migration safety
-- rule "split backfill from delete".
--
-- Additive, all-nullable, no defaults, no CHECK constraints. Safe to
-- apply against a populated table — existing rows land with the new
-- columns as NULL, which the template already tolerates via the
-- {% if tile_attribution_name %} guard.
--
-- Backfill of the new columns from the stock and dedicated manifests
-- runs as a separate one-shot script
-- (scripts/backfill_event_image_attribution.py). This migration only
-- opens the columns.

ALTER TABLE web.event_images
    ADD COLUMN attribution_name       VARCHAR(500),
    ADD COLUMN attribution_url        VARCHAR(500),
    ADD COLUMN attribution_source_url VARCHAR(500);
