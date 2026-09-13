import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

# Setup paths
_BACKEND_PATH = Path(__file__).resolve().parents[3]
if str(_BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(_BACKEND_PATH))

from app.database import Base
from app.models.asset import Asset
from app.models.component import Component
from app.models.maintenance_record import MaintenanceRecord
from app.models.prediction import Prediction
from app.models.anomaly import Anomaly
from app.models.mission import Mission
from app.models.readiness_result import ReadinessResult
from app.models.maintenance_recommendation import MaintenanceRecommendation

from app.services.readiness_integration import run_readiness_pipeline

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()

def test_missing_hours_since_service_raises_exception(db_session):
    # Setup data with missing hours_since_service (simulating legacy data)
    db_session.add(Asset(asset_id="AS-100", asset_name="Test Asset", asset_type="drone", unit="A"))
    db_session.add(Component(component_id="C-1", asset_id="AS-100", component_type="motor", criticality="HIGH"))
    db_session.add(Prediction(prediction_id="P-1", asset_id="AS-100", component_id="C-1", failure_probability=0.8, risk_category="HIGH", timestamp="2024-01-01T00:00:00"))
    
    mr = MaintenanceRecord(maintenance_id="M-1", asset_id="AS-100", component_id="C-1", maintenance_type="check", maintenance_date="2024-01-01", technician_action="none", status="OVERDUE", hours_since_service=100.0)
    db_session.add(mr)
    db_session.commit()

    # Modify it in memory to test the adapter validation without triggering DB constraints
    mr.hours_since_service = None 

    with db_session.no_autoflush:
        with pytest.raises(ValueError, match="Missing required maintenance field: 'hours_since_service'"):
            run_readiness_pipeline(db_session)

def test_run_readiness_pipeline_success(db_session):
    # Setup data
    db_session.add(Asset(asset_id="AS-100", asset_name="Test Asset", asset_type="drone", unit="A"))
    db_session.add(Component(component_id="C-1", asset_id="AS-100", component_type="motor", criticality="HIGH"))
    db_session.add(Prediction(prediction_id="P-1", asset_id="AS-100", component_id="C-1", failure_probability=0.8, risk_category="HIGH", timestamp="2024-01-01T00:00:00"))
    
    # Proper MaintenanceRecord with hours_since_service
    mr = MaintenanceRecord(maintenance_id="M-1", asset_id="AS-100", component_id="C-1", maintenance_type="check", maintenance_date="2024-01-01", technician_action="none", status="OVERDUE", hours_since_service=100.0)
    db_session.add(mr)
    
    db_session.add(Mission(mission_id="MSN-1", mission_name="Strike", mission_type="combat", criticality="HIGH", scheduled_time="2024-01-01T00:00:00", required_components='["motor"]', readiness_threshold=0.34))
    db_session.commit()

    summary = run_readiness_pipeline(db_session)

    assert summary["readiness_results_generated"] == 2  # 1 generic, 1 mission
    assert summary["maintenance_recommendations_generated"] == 1

    # Check persistence
    results = db_session.query(ReadinessResult).all()
    assert len(results) == 2
    assert any(r.mission_id is None for r in results)
    assert any(r.mission_id == "MSN-1" for r in results)

    recs = db_session.query(MaintenanceRecommendation).all()
    assert len(recs) == 1
    assert recs[0].component_id == "C-1"
    assert recs[0].priority == 1
