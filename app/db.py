import os

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# The pool is capped because this database is shared and small.
#
# Cloud SQL `db-f1-micro` allows 25 connections; 3 are reserved for
# superusers and 3 are held permanently by the Cloud SQL agent, leaving
# **19** for applications — this service plus the scraper's batch
# pipelines, which need 6-8 each while they run.
#
# SQLAlchemy's defaults are `pool_size=5, max_overflow=10`, so an
# uncapped engine allows 15 connections per instance. At `maxScale=5`
# that is 75 against a budget of 19.
#
# The idle case is worse than the burst. Overflow connections close on
# return, but the 5 pooled ones are held persistently once warmed, so
# after any traffic spike this service alone would hold 25 connections
# indefinitely -- over budget with the site doing nothing, and the
# scraper unable to connect at all.
#
# 2 per instance x 5 instances = 10 at peak and at idle, leaving 9.
#
# `max_overflow=0` means requests beyond 2 concurrent database users
# queue rather than opening more connections. Handlers are sync, so
# FastAPI runs them in a threadpool of ~40 -- `pool_timeout` is lowered
# from the 30s default so a saturated pool fails fast instead of tying
# up threads for half a minute.
#
# `pool_pre_ping` and `pool_recycle` are not optional extras here. Cloud
# SQL drops idle connections, and capping the pool makes each connection
# longer-lived; without these, exhaustion errors would simply be traded
# for stale-connection errors.
engine = create_engine(
    settings.database_url,
    pool_size=2,
    max_overflow=0,
    pool_timeout=10,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={
        # Without this the service's connections show as "(unnamed)" in
        # pg_stat_activity and cannot be told apart from anything else
        # sharing the instance.
        "application_name": f"indie-runners-web:{os.environ.get('K_REVISION', 'local')}",
    },
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    metadata = MetaData(schema="web")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
