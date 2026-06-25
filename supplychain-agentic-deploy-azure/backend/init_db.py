import os
import subprocess
import sys
import time

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from db import Base, engine, SessionLocal
from models import Supplier


def wait_for_database(max_attempts: int = 60, delay_seconds: int = 2) -> None:
    """Wait until the configured database accepts connections.

    ACA starts the backend and the Postgres sidecar at the same time, so the
    backend must not fail just because Postgres needs a few seconds to boot.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("Database connection ready")
            return
        except SQLAlchemyError as exc:
            if attempt == max_attempts:
                raise RuntimeError("Database did not become ready in time") from exc
            print(
                f"Database not ready yet; retrying {attempt}/{max_attempts} "
                f"in {delay_seconds}s..."
            )
            time.sleep(delay_seconds)


def seed_database_if_empty() -> None:
    db = SessionLocal()
    try:
        has_supplier_data = db.query(Supplier).first() is not None
    finally:
        db.close()

    if has_supplier_data:
        print("Database already seeded")
        return

    print("No supplier data found. Seeding demo supply-chain dataset...")
    seed_script = os.path.join(os.path.dirname(__file__), "seed_scenarios.py")
    subprocess.run([sys.executable, seed_script], check=True)
    print("Seed data loaded")


def init_db() -> None:
    wait_for_database()
    print("Creating tables if needed...")
    Base.metadata.create_all(bind=engine)
    seed_database_if_empty()


if __name__ == "__main__":
    init_db()
