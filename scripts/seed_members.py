"""
Seed script — inserts 50 realistic gym members into the database.

Run from the project root:
    python scripts/seed_members.py

Options:
    --dry-run   Print the records without inserting them.
    --delete    Delete ALL members whose member_code starts with 'MEM-SEED-'
                (rollback previously seeded data).

Notes:
    - Member codes use the prefix MEM-SEED- so they are easy to identify and clean up.
    - Members are a mix of active/inactive, genders, ages and cities.
    - Duplicate runs are safe: the script skips members whose code already exists.
"""

import sys
import os
import random
import string
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Make project root importable
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.database.manager import db_manager  # noqa: E402  (needs sys.path first)

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------
FIRST_NAMES_M = [
    "Carlos", "Luis", "Jose", "Miguel", "Juan", "Roberto", "Diego",
    "Fernando", "Eduardo", "Andres", "Ricardo", "Jorge", "Marco", "Ivan",
    "Alejandro", "Hector", "Adrian", "Gabriel", "Daniel", "Oscar",
]

FIRST_NAMES_F = [
    "Maria", "Ana", "Sofia", "Gabriela", "Fernanda", "Laura", "Monica",
    "Karla", "Valeria", "Diana", "Claudia", "Alejandra", "Paola", "Daniela",
    "Erika", "Brenda", "Adriana", "Jessica", "Natalia", "Veronica",
]

LAST_NAMES = [
    "Garcia", "Martinez", "Lopez", "Hernandez", "Gonzalez", "Perez",
    "Rodriguez", "Sanchez", "Ramirez", "Torres", "Flores", "Rivera",
    "Gomez", "Diaz", "Reyes", "Cruz", "Morales", "Ortiz", "Gutierrez",
    "Chavez", "Ramos", "Vargas", "Castillo", "Jimenez", "Mendoza",
]

CITIES = [
    "Ciudad Juarez", "Chihuahua", "El Paso", "Monterrey", "Torreon",
]

NOTES_OPTIONS = [
    "Prefers morning sessions.",
    "Interested in personal training.",
    "Has a knee injury — avoid high impact.",
    "Competitive powerlifter.",
    "Beginner — needs orientation.",
    "Referred by a current member.",
    "Works night shift, attends afternoons.",
    None,
    None,
    None,
]


def random_date_of_birth() -> str:
    """Returns a random date of birth for an adult between 18 and 65."""
    today = date.today()
    days_in_range = (65 - 18) * 365
    birth_date = today - timedelta(days=random.randint(18 * 365, 18 * 365 + days_in_range))
    return birth_date.isoformat()


def random_phone() -> str:
    return f"({random.randint(600,999)}) {random.randint(100,999)}-{random.randint(1000,9999)}"


def random_email(first: str, last: str, index: int) -> str:
    domains = ["gmail.com", "hotmail.com", "outlook.com", "yahoo.com"]
    base = f"{first.lower()}.{last.lower()}{index}"
    return f"{base}@{random.choice(domains)}"


def seed_code(index: int) -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"MEM-SEED-{index:03d}-{suffix}"


def build_members(n: int = 50) -> list[dict]:
    members = []
    random.seed(42)  # Reproducible output

    for i in range(1, n + 1):
        gender = random.choice(["male", "female"])
        first = random.choice(FIRST_NAMES_M if gender == "male" else FIRST_NAMES_F)
        last1 = random.choice(LAST_NAMES)
        last2 = random.choice(LAST_NAMES)
        last_name = f"{last1} {last2}"
        city = random.choice(CITIES)
        is_active = random.random() > 0.15  # ~85% active

        members.append({
            "member_code":              seed_code(i),
            "first_name":               first,
            "last_name":                last_name,
            "email":                    random_email(first, last1, i),
            "phone":                    random_phone(),
            "date_of_birth":            random_date_of_birth(),
            "gender":                   gender,
            "address":                  f"{random.randint(100, 9999)} Calle {random.choice(LAST_NAMES)}, {city}",
            "emergency_contact_name":   f"{random.choice(FIRST_NAMES_F)} {random.choice(LAST_NAMES)}",
            "emergency_contact_phone":  random_phone(),
            "notes":                    random.choice(NOTES_OPTIONS),
            "is_active":                is_active,
        })

    return members


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run(dry_run: bool = False, delete: bool = False) -> None:

    if delete:
        print("Deleting seeded members (member_code LIKE 'MEM-SEED-%') ...")
        try:
            rows = db_manager.client.table("members") \
                .select("id, member_code") \
                .like("member_code", "MEM-SEED-%") \
                .execute().data

            if not rows:
                print("  Nothing to delete.")
                return

            for row in rows:
                db_manager.delete("members", {"id": row["id"]})
                print(f"  Deleted: {row['member_code']}")

            print(f"\nDone. {len(rows)} member(s) removed.")
        except Exception as e:
            print(f"Error during delete: {e}")
        return

    members = build_members(50)

    if dry_run:
        print(f"DRY RUN — {len(members)} members would be inserted:\n")
        for m in members:
            active = "active" if m["is_active"] else "inactive"
            print(f"  {m['member_code']}  {m['first_name']} {m['last_name']}  <{m['email']}>  [{active}]")
        return

    print(f"Inserting {len(members)} members ...\n")
    inserted = 0
    skipped = 0

    for m in members:
        try:
            # Skip if code already exists
            existing = db_manager.select("members", filters={"member_code": m["member_code"]})
            if existing:
                print(f"  SKIP  {m['member_code']} (already exists)")
                skipped += 1
                continue

            db_manager.insert("members", m)
            active = "active" if m["is_active"] else "inactive"
            print(f"  OK    {m['member_code']}  {m['first_name']} {m['last_name']}  [{active}]")
            inserted += 1

        except Exception as e:
            print(f"  ERROR {m['member_code']}: {e}")

    print(f"\nDone. {inserted} inserted, {skipped} skipped.")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    delete  = "--delete"  in sys.argv
    run(dry_run=dry_run, delete=delete)
