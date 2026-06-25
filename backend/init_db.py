from db import Base, engine, SessionLocal
from models import Supplier


def init_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(Supplier).first():
            print("Database already seeded ✅")
        else:
            print("⚠️  No data found. Run: venv/bin/python seed_scenarios.py")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
