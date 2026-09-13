import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import json
import sys
from pathlib import Path

# Setup paths
_BACKEND_PATH = Path(__file__).resolve().parents[3]
if str(_BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(_BACKEND_PATH))

from app.main import app
from app.database import Base, get_db
from app.models.readiness_result import ReadinessResult

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

def test_mission_readiness_api_multiple_evidence():
    db = TestingSessionLocal()
    
    # Clear existing results
    db.query(ReadinessResult).delete()
    db.commit()
    
    # Insert a dummy ReadinessResult with multiple evidence objects (list of dicts)
    evidence_list = [
        {"asset_id": "AS-1047", "component": "bearing", "failure_risk": 0.899},
        {"asset_id": "AS-1047", "component": "engine", "failure_risk": 0.1}
    ]
    
    result = ReadinessResult(
        result_id="RDY-1047-MSN003",
        asset_id="AS-1047",
        mission_id="MSN-003",
        readiness_score=0.82,
        readiness_status="NOT_READY",
        reasons='["Bearing inspection is overdue"]',
        evidence=json.dumps(evidence_list),
        timestamp="2026-09-13T20:00:00Z"
    )
    
    db.add(result)
    db.commit()
    db.close()
    
    response = client.get("/missions/MSN-003/readiness")
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Find AS-1047 in the response
    item = next(d for d in data if d["asset_id"] == "AS-1047")
    assert item["readiness_status"] == "NOT_READY"
    assert isinstance(item["evidence"], list)
    assert len(item["evidence"]) == 2
    assert item["evidence"][0]["component"] == "bearing"
    assert item["evidence"][1]["component"] == "engine"
