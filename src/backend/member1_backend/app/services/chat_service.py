"""
AssetSentinel — IBM Bob Chat Service
src/backend/member1_backend/app/services/chat_service.py

Intent router for the grounded chatbot. All responses are sourced from
real database queries — no hardcoded asset-specific answers.

Newly added assets automatically become available because this service
queries SQLite, which is updated by the Add Asset pipeline.
"""

import json
import re
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.models.prediction import Prediction
from app.models.anomaly import Anomaly
from app.models.readiness_result import ReadinessResult
from app.models.maintenance_recommendation import MaintenanceRecommendation


# ===========================================================================
# Fleet-level tools
# ===========================================================================

def get_fleet_readiness(db: Session) -> str:
    total = db.query(Asset).count()
    ready = db.query(Asset).filter(Asset.current_status == "READY").count()
    not_ready = db.query(Asset).filter(Asset.current_status == "NOT_READY").count()
    cond = db.query(Asset).filter(Asset.current_status == "CONDITIONALLY_READY").count()

    pct = round((ready / total) * 100) if total > 0 else 0
    return (
        f"Current fleet readiness: {ready} of {total} assets are READY ({pct}%). "
        f"{not_ready} asset(s) are NOT_READY. {cond} asset(s) are CONDITIONALLY_READY."
    )


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
    return (
        f"Detected {len(high_anom)} high-severity anomalies affecting assets: "
        f"{', '.join(assets)}. These assets should be inspected immediately."
    )


def get_predictions_summary(db: Session) -> str:
    high_preds = db.query(Prediction).filter(Prediction.risk_category == "HIGH").all()
    if not high_preds:
        return "There are no high-risk failure predictions at this time."

    parts = [
        f"{p.asset_id} ({p.component_id}): {round(p.failure_probability * 100, 1)}% failure probability"
        for p in high_preds[:3]
    ]
    return f"Detected {len(high_preds)} high-risk components. Top risks:\n" + "\n".join(parts)


# ===========================================================================
# Asset-specific tools
# ===========================================================================

def _extract_asset_id(text: str) -> str | None:
    """Extract an asset ID pattern (e.g. AS-1047, AS-2001) from the message."""
    match = re.search(r"\bAS-\d{3,6}\b", text.upper())
    return match.group(0) if match else None


def get_asset_readiness_explanation(db: Session, asset_id: str) -> str:
    """
    Return a grounded readiness explanation for a specific asset.
    Sourced entirely from ReadinessResult.reasons in the database.
    """
    asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
    if not asset:
        return (
            f"Asset '{asset_id}' was not found in the database. "
            "If you just added it, please ensure the analysis completed successfully."
        )

    rdy = (
        db.query(ReadinessResult)
        .filter(ReadinessResult.asset_id == asset_id, ReadinessResult.mission_id == None)  # noqa: E711
        .first()
    )

    status = asset.current_status
    score_pct = round((asset.readiness_score or 0.0) * 100, 1)

    if not rdy:
        return (
            f"Asset {asset_id} has status {status} (readiness index: {score_pct}%). "
            "No detailed readiness analysis is available yet. "
            "Try running the ML and readiness pipelines from the Dashboard."
        )

    reasons: list[str] = []
    try:
        reasons = json.loads(rdy.reasons) if rdy.reasons else []
    except (json.JSONDecodeError, TypeError):
        pass

    reason_text = ""
    if reasons:
        reason_text = " Reasons:\n• " + "\n• ".join(reasons)
    else:
        reason_text = " No specific reason flags were recorded."

    return (
        f"Asset {asset_id} is {status} with a readiness score of {score_pct}%.{reason_text}"
    )


def get_asset_risk_summary(db: Session, asset_id: str) -> str:
    """Return ML risk and anomaly summary for a specific asset."""
    asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
    if not asset:
        return f"Asset '{asset_id}' not found in the database."

    pred = (
        db.query(Prediction)
        .filter(Prediction.asset_id == asset_id)
        .order_by(Prediction.timestamp.desc())
        .first()
    )
    anom = (
        db.query(Anomaly)
        .filter(Anomaly.asset_id == asset_id)
        .order_by(Anomaly.timestamp.desc())
        .first()
    )

    if not pred:
        return f"No ML prediction is available for asset {asset_id} yet."

    prob_pct = round(pred.failure_probability * 100, 1)
    msg = (
        f"Asset {asset_id}: Failure probability {prob_pct}%, risk category {pred.risk_category}."
    )
    if anom:
        msg += (
            f" Anomaly status: {anom.anomaly_status} (severity: {anom.anomaly_severity}"
            + (f", sensor: {anom.sensor}" if anom.sensor != "NONE" else "") + ")."
        )
    return msg


def get_asset_maintenance_summary(db: Session, asset_id: str) -> str:
    """Return maintenance recommendations for a specific asset."""
    asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
    if not asset:
        return f"Asset '{asset_id}' not found in the database."

    recs = (
        db.query(MaintenanceRecommendation)
        .filter(MaintenanceRecommendation.asset_id == asset_id)
        .order_by(MaintenanceRecommendation.priority)
        .all()
    )

    if not recs:
        return f"No maintenance recommendations are currently on record for asset {asset_id}."

    parts = [
        f"Priority {r.priority}: {r.action} (urgency: {r.urgency}, risk: {r.risk})"
        for r in recs[:3]
    ]
    return f"Maintenance recommendations for {asset_id}:\n" + "\n".join(parts)


# ===========================================================================
# Intent router
# ===========================================================================

def process_chat_message(message: str, db: Session) -> str:
    text = message.lower()

    # ── Asset-specific queries (highest priority) ──────────────────────────
    asset_id = _extract_asset_id(message)
    if asset_id:
        if any(k in text for k in ["why", "not ready", "readiness", "status", "explain", "evidence", "reason"]):
            return get_asset_readiness_explanation(db, asset_id)

        if any(k in text for k in ["risk", "probability", "failure", "anomaly", "anomalies"]):
            return get_asset_risk_summary(db, asset_id)

        if any(k in text for k in ["maintenance", "service", "repair", "fix", "recommendation"]):
            return get_asset_maintenance_summary(db, asset_id)

        # Generic asset query — return readiness as default
        return get_asset_readiness_explanation(db, asset_id)

    # ── Fleet-level queries ────────────────────────────────────────────────
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
        "I am IBM BOB. I can explain fleet health, asset risk, maintenance priorities, "
        "mission readiness, and active warnings using live backend data. "
        "You can also ask about a specific asset by ID — for example: "
        "'Why is AS-2002 not ready?' or 'What is the risk for AS-1047?'"
    )
