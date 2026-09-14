import json
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.models.component import Component
from app.models.sensor_data import SensorData
from app.models.prediction import Prediction
from app.models.anomaly import Anomaly
from app.models.maintenance_record import MaintenanceRecord
from app.models.maintenance_recommendation import MaintenanceRecommendation
from app.models.readiness_result import ReadinessResult
from app.models.mission import Mission

def get_asset_status_tool(db: Session, asset_id: str) -> str:
    """Returns the status, metadata, and latest readiness result for an asset."""
    asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
    if not asset:
        return f"Asset {asset_id} not found."
    
    readiness = db.query(ReadinessResult).filter(ReadinessResult.asset_id == asset_id).order_by(ReadinessResult.timestamp.desc()).first()
    
    result = {
        "asset_id": asset.asset_id,
        "name": asset.asset_name,
        "type": asset.asset_type,
        "unit": asset.unit,
        "status": asset.current_status,
        "latest_readiness_score": asset.readiness_score,
        "latest_readiness_reasons": readiness.reasons if readiness else None
    }
    return json.dumps(result, indent=2)

def get_asset_details_tool(db: Session, asset_id: str) -> str:
    """Returns detailed asset information including components, criticality, and operational hours."""
    asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
    if not asset:
        return f"Asset {asset_id} not found."
        
    components = db.query(Component).filter(Component.asset_id == asset_id).all()
    
    result = {
        "asset_id": asset.asset_id,
        "operational_hours": asset.operational_hours,
        "components": [
            {
                "component_id": c.component_id,
                "type": c.component_type,
                "criticality": c.criticality,
                "operating_hours": c.operating_hours,
                "life_limit": c.life_limit
            } for c in components
        ]
    }
    return json.dumps(result, indent=2)

def get_sensor_trends_tool(db: Session, asset_id: str) -> str:
    """Returns recent sensor readings and trend information for an asset."""
    readings = db.query(SensorData).filter(SensorData.asset_id == asset_id).order_by(SensorData.timestamp.desc()).limit(10).all()
    if not readings:
        return f"No sensor data found for {asset_id}."
        
    result = [
        {
            "timestamp": str(r.timestamp),
            "vibration": r.vibration,
            "temperature": r.temperature,
            "pressure": r.pressure,
            "rpm": r.rpm
        } for r in readings
    ]
    return json.dumps(result, indent=2)

def get_component_health_tool(db: Session, asset_id: str) -> str:
    """Returns component health and service hours for all components in an asset."""
    components = db.query(Component).filter(Component.asset_id == asset_id).all()
    if not components:
        return f"No components found for asset {asset_id}."
        
    result = []
    for c in components:
        maintenance = db.query(MaintenanceRecord).filter(
            MaintenanceRecord.component_id == c.component_id,
            MaintenanceRecord.status == "COMPLETED"
        ).order_by(MaintenanceRecord.maintenance_date.desc()).first()
        
        result.append({
            "component_id": c.component_id,
            "type": c.component_type,
            "operating_hours": c.operating_hours,
            "life_limit": c.life_limit,
            "health_percentage": round(100.0 * (1 - c.operating_hours / c.life_limit), 2) if c.life_limit else None,
            "last_service_hours": maintenance.hours_since_service if maintenance else c.operating_hours
        })
    return json.dumps(result, indent=2)

def get_failure_predictions_tool(db: Session, asset_id: str) -> str:
    """Returns component failure predictions, probability, and risk level."""
    predictions = db.query(Prediction).filter(Prediction.asset_id == asset_id).order_by(Prediction.timestamp.desc()).limit(10).all()
    if not predictions:
        return f"No predictions found for asset {asset_id}."
        
    latest = {}
    for p in predictions:
        if p.component_id not in latest:
            latest[p.component_id] = p
            
    result = [
        {
            "component_id": p.component_id,
            "failure_probability": p.failure_probability,
            "risk_category": p.risk_category,
            "timestamp": str(p.timestamp)
        } for p in latest.values()
    ]
    return json.dumps(result, indent=2)

def get_anomalies_tool(db: Session, asset_id: str) -> str:
    """Returns recent sensor anomalies, severity, and scores."""
    anomalies = db.query(Anomaly).filter(Anomaly.asset_id == asset_id).order_by(Anomaly.timestamp.desc()).limit(10).all()
    if not anomalies:
        return f"No anomalies found for asset {asset_id}."
        
    result = [
        {
            "component_id": a.component_id,
            "anomaly_score": a.anomaly_score,
            "anomaly_status": a.anomaly_status,
            "anomaly_severity": a.anomaly_severity,
            "sensor": a.sensor,
            "timestamp": str(a.timestamp)
        } for a in anomalies
    ]
    return json.dumps(result, indent=2)

def get_maintenance_history_tool(db: Session, asset_id: str) -> str:
    """Returns service records, inspection status, and overdue status."""
    records = db.query(MaintenanceRecord).filter(MaintenanceRecord.asset_id == asset_id).order_by(MaintenanceRecord.maintenance_date.desc()).all()
    if not records:
        return f"No maintenance records found for asset {asset_id}."
        
    result = [
        {
            "maintenance_id": r.maintenance_id,
            "component_id": r.component_id,
            "type": r.maintenance_type,
            "date": str(r.maintenance_date),
            "action": r.technician_action,
            "status": r.status,
            "hours_since_service": r.hours_since_service
        } for r in records
    ]
    return json.dumps(result, indent=2)

def get_mission_readiness_tool(db: Session, asset_id: str, mission_id: str) -> str:
    """Returns readiness status, score, reasons, and evidence for a specific mission."""
    result = db.query(ReadinessResult).filter(
        ReadinessResult.asset_id == asset_id,
        ReadinessResult.mission_id == mission_id
    ).order_by(ReadinessResult.timestamp.desc()).first()
    
    if not result:
        return f"No readiness result found for {asset_id} on mission {mission_id}."
        
    res_dict = {
        "status": result.readiness_status,
        "score": result.readiness_score,
        "reasons": json.loads(result.reasons) if isinstance(result.reasons, str) else result.reasons,
        "evidence": json.loads(result.evidence_data) if isinstance(result.evidence_data, str) else result.evidence_data,
        "timestamp": str(result.timestamp)
    }
    return json.dumps(res_dict, indent=2)

def get_fleet_readiness_tool(db: Session) -> str:
    """Returns fleet summary, ready count, conditional count, and not ready count."""
    total = db.query(Asset).count()
    ready = db.query(Asset).filter(Asset.current_status == "READY").count()
    cond = db.query(Asset).filter(Asset.current_status == "CONDITIONALLY_READY").count()
    not_ready = db.query(Asset).filter(Asset.current_status == "NOT_READY").count()
    
    result = {
        "total_assets": total,
        "ready": ready,
        "conditionally_ready": cond,
        "not_ready": not_ready
    }
    return json.dumps(result, indent=2)

def get_maintenance_priorities_tool(db: Session) -> str:
    """Returns ranked maintenance recommendations, urgency, priority score, and actions."""
    recs = db.query(MaintenanceRecommendation).order_by(MaintenanceRecommendation.priority).limit(10).all()
    if not recs:
        return "No maintenance recommendations found."
        
    result = [
        {
            "asset_id": r.asset_id,
            "component_id": r.component_id,
            "action": r.action,
            "urgency": r.urgency,
            "priority_score": r.priority,
            "reason": r.reason,
            "timestamp": str(r.timestamp)
        } for r in recs
    ]
    return json.dumps(result, indent=2)

def get_mission_details_tool(db: Session, mission_id: str) -> str:
    """Returns mission requirements, criticality, and relevant thresholds."""
    mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
    if not mission:
        return f"Mission {mission_id} not found."
        
    result = {
        "mission_id": mission.mission_id,
        "name": mission.mission_name,
        "type": mission.mission_type,
        "criticality": mission.criticality,
        "scheduled_time": str(mission.scheduled_time),
        "required_components": json.loads(mission.required_components) if mission.required_components else [],
        "readiness_threshold": mission.readiness_threshold
    }
    return json.dumps(result, indent=2)
