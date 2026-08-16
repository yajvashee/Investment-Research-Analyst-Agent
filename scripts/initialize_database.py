"""Create the Phase 2 table and add the small sample dataset."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.database.connection import create_database_tables
from app.database.seed import seed_sample_data


def main() -> None:
    create_database_tables()
    inserted_count = seed_sample_data()
    print(f"Database is ready. Added {inserted_count} sample record(s).")


if __name__ == "__main__":
    main()
