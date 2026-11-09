-- Migration 001: Create web schema and tables owned by indie-runners-web

CREATE SCHEMA IF NOT EXISTS web;

CREATE TABLE IF NOT EXISTS web.users (
    id                 BIGSERIAL PRIMARY KEY,
    strava_athlete_id  BIGINT    NOT NULL UNIQUE,
    firstname          TEXT,
    lastname           TEXT,
    profile_photo_url  TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS web.attendance (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT      NOT NULL REFERENCES web.users(id) ON DELETE CASCADE,
    race_id    BIGINT      NOT NULL,
    status     TEXT        NOT NULL CHECK (status IN ('going', 'interested')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, race_id)
);

-- race_id is a soft foreign key: core.races is owned by indie-runners-scraper
-- and we do not enforce referential integrity at the database level
CREATE INDEX IF NOT EXISTS idx_attendance_race_id ON web.attendance(race_id);
