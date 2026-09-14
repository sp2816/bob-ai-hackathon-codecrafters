from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.models.prediction import Prediction
from app.models.anomaly import Anomaly
from app.models.readiness_result import ReadinessResult
from app.models.maintenance_recommendation import MaintenanceRecommendation

# -- Mock MCP Tools --

def get_fleet_readiness(db: Session) -> str:
    total = db.query(Asset).count()
    ready = db.query(Asset).filter(Asset.current_status == "READY").count()
    not_ready = db.query(Asset).filter(Asset.current_status == "NOT_READY").count()
    cond = db.query(Asset).filter(Asset.current_status == "CONDITIONALLY_READY").count()
    
    pct = round((ready / total) * 100) if total > 0 else 0
    return f"Current fleet readiness: {ready} of {total} assets are READY ({pct}%). {not_ready} asset(s) are NOT_READY. {cond} asset(s) are CONDITIONALLY_READY."

def get_maintenance_priorities(db: Session) -> str:
    recs = db.query(MaintenanceRecommendation).order_by(MaintenanceRecommendation.priority).limit(3).all()
    if not recs:
        return "No maintenance recommendations are currently queued."
    
    parts = [f"{r.asset_id} / {r.component_id} — {r.action} (urgency: {r.urgency})" for r in recs]
    return f"Top {len(parts)} maintenance priority item(s):\n" + "\n".join(parts)

def get_warnings(db: Session) -> str:
    not_ready = db.query(Asset).filter(Asset.current_status == "NOT_READY").count()
    if not_ready == 0:
        return "No assets are currently flagged as NOT_READY. The fleet is operating within acceptable thresholds."
    
    top_rec = db.query(MaintenanceRecommendation).filter(MaintenanceRecommendation.urgency == "HIGH").first()
    msg = f"{not_ready} asset(s) are currently NOT_READY. "
    if top_rec:
        msg += f"Highest priority action: {top_rec.action} for {top_rec.asset_id} / {top_rec.component_id}."
    else:
        msg += "Check the Maintenance page for prioritized recommendations."
    return msg
    
def get_anomalies_summary(db: Session) -> str:
    high_anom = db.query(Anomaly).filter(Anomaly.anomaly_severity == "HIGH").all()
    if not high_anom:
        return "There are no high-severity anomalies currently detected."
    
    assets = list(set([a.asset_id for a in high_anom]))
    return f"Detected {len(high_anom)} high-severity anomalies affecting assets: {', '.join(assets)}. These assets should be inspected immediately."

def get_predictions_summary(db: Session) -> str:
    high_preds = db.query(Prediction).filter(Prediction.risk_category == "HIGH").all()
    if not high_preds:
        return "There are no high-risk failure predictions at this time."
    
    parts = [f"{p.asset_id} ({p.component_id}): {round(p.failure_probability * 100, 1)}% failure probability" for p in high_preds[:3]]
    return f"Detected {len(high_preds)} high-risk components. Top risks:\n" + "\n".join(parts)

# -- Intent Router --

def process_chat_message(message: str, db: Session) -> str:
    text = message.lower()
    
    # Intent Mapping
    if any(k in text for k in ["anomaly", "anomalies", "vibration", "temperature", "sensor"]):
        return get_anomalies_summary(db)
        
    if any(k in text for k in ["prediction", "probability", "failure risk"]):
        return get_predictions_summary(db)
        
    if any(k in text for k in ["readiness", "ready", "fleet", "status"]):
        return get_fleet_readiness(db)
        
    if any(k in text for k in ["attention", "focus", "priority", "maintenance", "service", "repair", "fix"]):
        return get_maintenance_priorities(db)
        
    if any(k in text for k in ["warning", "alert", "risk"]):
        return get_warnings(db)
        
    return (
        "I am IBM BOB. I can help explain fleet health, asset risk, maintenance priorities, "
        "mission readiness, and active warnings using real data from the backend. "
        "Please ask about readiness, maintenance, predictions, or anomalies."
    )
