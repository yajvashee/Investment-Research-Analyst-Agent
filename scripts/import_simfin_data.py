"""Import the downloaded SimFin annual ZIP files into PostgreSQL."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.database.connection import create_database_tables, get_session
from app.database.simfin_import import import_simfin_annual_data


def main() -> None:
    create_database_tables()
    with get_session() as session:
        result = import_simfin_annual_data(PROJECT_ROOT / "data" / "sample" / "simfin", session)
    print(f"SimFin import complete: {result.inserted} added, {result.updated} updated, {result.skipped} skipped.")


if __name__ == "__main__":
    main()
