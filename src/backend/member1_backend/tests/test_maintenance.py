import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

Base.metadata.create_all(bind=test_engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def seed_test_data():
    from app.models.maintenance_record import MaintenanceRecord
    db = TestingSessionLocal()
    if not db.get(MaintenanceRecord, "MNT-1047-001"):
        db.add(MaintenanceRecord(
            maintenance_id="MNT-1047-001",
            asset_id="AS-1047",
            component_id="BRG-1047",
            maintenance_type="inspection",
            maintenance_date="2024-02-10",
            technician_action="Routine bearing inspection — passed",
            status="OVERDUE",
            notes="Last service 420h ago. Next inspection overdue.",
        ))
        db.commit()
    db.close()
    yield


def test_list_maintenance_for_asset():
    response = client.get("/maintenance/AS-1047")
    assert response.status_code == 200
    records = response.json()
    assert isinstance(records, list)
    assert any(r["maintenance_id"] == "MNT-1047-001" for r in records)


def test_maintenance_status_is_overdue():
    response = client.get("/maintenance/AS-1047")
    records = response.json()
    overdue = [r for r in records if r["status"] == "OVERDUE"]
    assert len(overdue) >= 1


def test_maintenance_field_names():
    """Verify all contract-required field names are present in response."""
    response = client.get("/maintenance/AS-1047")
    record = response.json()[0]
    for field in ["maintenance_id", "asset_id", "component_id", "maintenance_type",
                  "maintenance_date", "technician_action", "status"]:
        assert field in record, f"Missing field: {field}"
