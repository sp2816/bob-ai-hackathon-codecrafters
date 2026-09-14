import datetime
from sqlalchemy.orm import Session
from app.models.prediction import Prediction
from app.models.anomaly import Anomaly
from app.models.readiness_result import ReadinessResult
from app.models.maintenance_recommendation import MaintenanceRecommendation
from app.schemas.notification import Notification

def get_all_notifications(db: Session) -> list[Notification]:
    notifications = []

    # 1. High Failure Risk Predictions
    high_preds = db.query(Prediction).filter(Prediction.risk_category == "HIGH").all()
    for p in high_preds:
        notifications.append(
            Notification(
                id=f"NOTIF-PRED-{p.prediction_id}",
                title="High Failure Risk Detected",
                message=f"High failure risk detected for {p.component_id} on {p.asset_id}.",
                severity="HIGH",
                source="PREDICTION",
                asset_id=p.asset_id,
                timestamp=p.timestamp
            )
        )

    # 2. Critical Anomalies
    crit_anoms = db.query(Anomaly).filter(Anomaly.anomaly_severity == "HIGH").all()
    for a in crit_anoms:
        notifications.append(
            Notification(
                id=f"NOTIF-ANOM-{a.anomaly_id}",
                title="Critical Anomaly Detected",
                message=f"High severity anomaly detected on {a.asset_id} via {a.sensor} sensor.",
                severity="CRITICAL",
                source="ANOMALY",
                asset_id=a.asset_id,
                timestamp=a.timestamp
            )
        )

    # 3. Readiness Results
    not_ready = db.query(ReadinessResult).filter(ReadinessResult.readiness_status == "NOT_READY").all()
    for r in not_ready:
        notifications.append(
            Notification(
                id=f"NOTIF-READY-{r.result_id}",
                title="Mission Readiness Alert",
                message=f"{r.asset_id} is currently NOT READY for mission {r.mission_id}.",
                severity="HIGH",
                source="READINESS",
                asset_id=r.asset_id,
                timestamp=r.timestamp
            )
        )
        
    cond_ready = db.query(ReadinessResult).filter(ReadinessResult.readiness_status == "CONDITIONALLY_READY").all()
    for r in cond_ready:
        notifications.append(
            Notification(
                id=f"NOTIF-READY-{r.result_id}",
                title="Conditionally Ready Warning",
                message=f"{r.asset_id} is CONDITIONALLY READY for mission {r.mission_id}.",
                severity="MEDIUM",
                source="READINESS",
                asset_id=r.asset_id,
                timestamp=r.timestamp
            )
        )

    # 4. Maintenance Recommendations
    high_maint = db.query(MaintenanceRecommendation).filter(MaintenanceRecommendation.urgency == "HIGH").all()
    for m in high_maint:
        notifications.append(
            Notification(
                id=f"NOTIF-MAINT-{m.recommendation_id}",
                title="Maintenance Required",
                message=f"Immediate maintenance required for {m.asset_id}: {m.action}.",
                severity="HIGH",
                source="MAINTENANCE",
                asset_id=m.asset_id,
                timestamp=datetime.datetime.utcnow().isoformat() + "Z"
            )
        )

    # Sort descending by timestamp
    notifications.sort(key=lambda x: x.timestamp, reverse=True)
    return notifications
