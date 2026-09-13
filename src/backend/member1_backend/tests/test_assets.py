import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.asset import Asset
from app.models.component import Component

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def override_db_dependency():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


Base.metadata.create_all(bind=test_engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def seed_test_data():
    from app.models.asset import Asset
    db = TestingSessionLocal()
    if not db.get(Asset, "AS-1047"):
        db.add(Asset(
            asset_id="AS-1047",
            asset_name="Aircraft 1047",
            asset_type="aircraft",
            unit="Unit-A",
            operational_hours=2450.0,
            current_status="NOT_READY",
            readiness_score=None,
        ))
        db.commit()
    db.close()
    yield
    # teardown — leave data in place for inspection


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_assets_returns_200():
    response = client.get("/assets/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_asset_by_id():
    response = client.get("/assets/AS-1047")
    assert response.status_code == 200
    data = response.json()
    assert data["asset_id"] == "AS-1047"
    assert data["asset_type"] == "aircraft"
    assert data["current_status"] == "NOT_READY"


def test_get_asset_not_found():
    response = client.get("/assets/DOES-NOT-EXIST")
    assert response.status_code == 404
