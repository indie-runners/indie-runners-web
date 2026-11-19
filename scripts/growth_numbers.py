"""Read-only: prints the crew-growth numbers (#51, #53, docs/PLAN.md).

One connection, a READ ONLY transaction, SELECTs only. Output goes to
stdout; it carries user counts, so it belongs in exports/evidence/, never
in a tracked file (docs/roles/README.md § Boundaries).

The operator's user id comes from --operator-id or GROWTH_OPERATOR_ID and
is never written here.

    python3 scripts/growth_numbers.py --operator-id <id>
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.db import SessionLocal


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--operator-id", type=int, default=os.environ.get("GROWTH_OPERATOR_ID"))
    args = parser.parse_args()
    if args.operator_id is None:
        parser.error("pass --operator-id or set GROWTH_OPERATOR_ID")
    operator_id = int(args.operator_id)

    db = SessionLocal()
    try:
        db.execute(text("SET TRANSACTION READ ONLY"))
        users = db.execute(text("SELECT count(*) FROM web.users")).scalar_one()
        crews_5 = db.execute(text("""
            SELECT count(*) FROM (
                SELECT crew_id FROM web.crew_memberships GROUP BY crew_id HAVING count(*) >= 5
            ) c
        """)).scalar_one()
        crews_not_op = db.execute(
            text("SELECT count(*) FROM web.crews WHERE created_by <> :op"), {"op": operator_id}
        ).scalar_one()
        planners = db.execute(text("""
            SELECT count(DISTINCT a.user_id)
            FROM web.attendance a
            WHERE EXISTS (
                SELECT 1 FROM core.v_denormalized_event_data_upcoming v
                WHERE v.occurrence_id = a.occurrence_id::text
            )
        """)).scalar_one()
        weeks = db.execute(text("""
            SELECT w.week::date AS week, count(u.id) AS n
            FROM generate_series(date_trunc('week', now()) - interval '7 weeks',
                                 date_trunc('week', now()), interval '1 week') AS w(week)
            LEFT JOIN web.users u ON date_trunc('week', u.created_at) = w.week
            GROUP BY w.week ORDER BY w.week
        """)).all()
        # Needs migration 016 (#53). Users from before it have no source.
        by_source = db.execute(text("""
            SELECT date_trunc('week', created_at)::date AS week,
                   COALESCE(signup_source, '(none)') AS source,
                   COALESCE(signup_campaign, '') AS campaign, count(*) AS n
            FROM web.users
            WHERE created_at >= date_trunc('week', now()) - interval '7 weeks'
            GROUP BY 1, 2, 3 ORDER BY 1, 4 DESC, 2, 3
        """)).all()
    finally:
        db.rollback()
        db.close()

    share = f"{planners / users:.0%}" if users else "n/a"
    print(f"growth numbers, {date.today().isoformat()}")
    print(f"1. users: {users}")
    print(f"2. crews with 5+ members: {crews_5}")
    print(f"3. crews created by someone other than the operator: {crews_not_op}")
    print(f"4. users planning an upcoming race: {planners}/{users} ({share})")
    print("5. new users per ISO week (last 8):")
    for row in weeks:
        y, wk, _ = row.week.isocalendar()
        print(f"   {y}-W{wk:02d} (from {row.week.isoformat()}): {row.n}")
    print("6. new users per ISO week by source and campaign (last 8):")
    for row in by_source:
        y, wk, _ = row.week.isocalendar()
        campaign = f" / {row.campaign}" if row.campaign else ""
        print(f"   {y}-W{wk:02d}: {row.source}{campaign}: {row.n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
