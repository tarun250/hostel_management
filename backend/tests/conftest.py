import os

# Point the app at in-memory SQLite before anything imports app.db.
# Tests never touch the real PostgreSQL database.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def make_student(client):
    counter = {"n": 0}

    def _make(**overrides):
        counter["n"] += 1
        n = counter["n"]
        payload = {
            "roll_no": f"24BCS{n:04d}",
            "full_name": f"Student {n}",
            "email": f"student{n}@college.edu",
            "course": "B.Tech CSE",
            "year": 2,
        }
        payload.update(overrides)
        resp = client.post("/api/students", json=payload)
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


@pytest.fixture()
def make_room(client):
    def _make(number="A-101", capacity=2, **overrides):
        payload = {"number": number, "block": "A", "floor": 1, "capacity": capacity, "monthly_rent": 4500}
        payload.update(overrides)
        resp = client.post("/api/rooms", json=payload)
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make
