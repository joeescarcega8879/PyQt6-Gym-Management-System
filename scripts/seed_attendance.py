"""
Seed script — inserts realistic attendance records into Supabase.

Run from the project root:
    python scripts/seed_attendance.py

Options:
    --dry-run     Print the records without inserting them.
    --delete      Delete ALL attendance records whose notes contain '[SEED]'.
    --days N      Number of past days to generate records for (default: 30).

What gets generated (per day, randomly):
    - 8 to 18 check-ins spread across the day (06:00–21:00 local time).
    - ~80% of check-ins also have a check-out (1h–2.5h later).
    - ~20% are still "open" (no check-out) — useful for checkout button tests.
    - Some members appear on multiple days — realistic repeat visitors.
    - Today's records are always included so the default view is populated.

Requirements:
    - At least 10 active members must already exist in the database.
      Run scripts/seed_members.py first if needed.
"""

import sys
import os
import random
from datetime import date, datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Make project root importable
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.database.manager import db_manager  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
LOCAL_TZ = datetime.now().astimezone().tzinfo  # system local timezone


def local_dt(d: date, hour: int, minute: int) -> datetime:
    """Returns a timezone-aware datetime in local time, converted to UTC."""
    local = datetime(d.year, d.month, d.day, hour, minute, 0, tzinfo=LOCAL_TZ)
    return local.astimezone(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat()


def fetch_active_members() -> list[dict]:
    """Fetches all active members from the database."""
    rows = db_manager.select("members", columns="id, member_code, first_name, last_name",
                              filters={"is_active": True})
    return rows


def build_checkin_slots(day: date, count: int) -> list[tuple[datetime, datetime | None]]:
    """
    Returns `count` (check_in, check_out | None) pairs for the given day.
    Check-ins are spread between 06:00 and 21:00.
    """
    random.seed(int(day.strftime("%Y%m%d")))  # reproducible per day
    slots = []

    for _ in range(count):
        # Random check-in time between 06:00 and 20:00
        ci_hour   = random.randint(6, 20)
        ci_minute = random.randint(0, 59)
        check_in  = local_dt(day, ci_hour, ci_minute)

        # ~80% have a check-out
        if random.random() < 0.80:
            duration_minutes = random.randint(45, 150)
            check_out = check_in + timedelta(minutes=duration_minutes)
            # Don't let check-out go past 22:00 local
            max_co = local_dt(day, 22, 0)
            if check_out > max_co:
                check_out = max_co
        else:
            check_out = None

        slots.append((check_in, check_out))

    return slots


def build_records(members: list[dict], days: int) -> list[dict]:
    records = []
    today = date.today()
    random.seed(99)  # outer seed for member selection

    for offset in range(days - 1, -1, -1):  # oldest → newest
        day = today - timedelta(days=offset)
        daily_count = random.randint(8, 18)

        # Pick a random subset of members for this day (allow repeats across days, not within)
        day_members = random.sample(members, min(daily_count, len(members)))

        slots = build_checkin_slots(day, len(day_members))

        for member, (check_in, check_out) in zip(day_members, slots):
            record: dict = {
                "member_id":     member["id"],
                "check_in_time": iso(check_in),
                "notes":         "[SEED]",
            }
            if check_out:
                record["check_out_time"] = iso(check_out)

            records.append(record)

    return records


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run(dry_run: bool = False, delete: bool = False, days: int = 30) -> None:

    if delete:
        print("Deleting seeded attendance records (notes = '[SEED]') ...")
        try:
            rows = db_manager.select("attendance", columns="id", filters={"notes": "[SEED]"})
            if not rows:
                print("  Nothing to delete.")
                return
            for row in rows:
                db_manager.delete("attendance", {"id": row["id"]})
            print(f"\nDone. {len(rows)} record(s) removed.")
        except Exception as e:
            print(f"Error during delete: {e}")
        return

    # Fetch members
    print("Fetching active members ...")
    members = fetch_active_members()
    if len(members) < 5:
        print(
            f"ERROR: Only {len(members)} active member(s) found.\n"
            "Run scripts/seed_members.py first to populate the members table."
        )
        sys.exit(1)

    print(f"Found {len(members)} active members. Building {days} days of attendance ...\n")
    records = build_records(members, days)

    if dry_run:
        print(f"DRY RUN — {len(records)} records would be inserted:\n")
        for r in records:
            co = r.get("check_out_time", "open")
            print(f"  member={r['member_id'][:8]}...  in={r['check_in_time'][11:16]}  out={str(co)[11:16] if co != 'open' else 'open'}")
        return

    print(f"Inserting {len(records)} attendance records ...\n")
    inserted = 0

    for r in records:
        try:
            db_manager.insert("attendance", r)
            co_label = r.get("check_out_time", "open")[11:16] if r.get("check_out_time") else "open"
            print(f"  OK  member={r['member_id'][:8]}...  in={r['check_in_time'][11:16]}  out={co_label}")
            inserted += 1
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\nDone. {inserted} / {len(records)} records inserted.")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    delete  = "--delete"  in sys.argv

    days = 30
    for arg in sys.argv:
        if arg.startswith("--days="):
            try:
                days = int(arg.split("=")[1])
            except ValueError:
                print("Invalid --days value, using default 30.")

    run(dry_run=dry_run, delete=delete, days=days)
