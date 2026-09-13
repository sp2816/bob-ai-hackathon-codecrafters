# ─────────────────────────────────────────────────────────────────────────────
# AssetSentinel — Central Configuration
#
# ALL readiness weights, thresholds, and maintenance priority weights live here.
# Member 3 READS from this file; Member 1 OWNS it.
# Never hardcode these values anywhere else in the codebase.
# ─────────────────────────────────────────────────────────────────────────────

# ── Readiness Score Weights ───────────────────────────────────────────────────
# Score = W_FAILURE_RISK×failure_risk + W_ANOMALY×anomaly_severity
#       + W_CRITICALITY×criticality + W_MISSION_IMPACT×mission_impact
READINESS_W_FAILURE_RISK: float = 0.40
READINESS_W_ANOMALY_SEVERITY: float = 0.25
READINESS_W_CRITICALITY: float = 0.20
READINESS_W_MISSION_IMPACT: float = 0.15

# ── Readiness Status Thresholds ───────────────────────────────────────────────
# 0.00 – THRESHOLD_READY        → READY
# THRESHOLD_READY – THRESHOLD_NOT_READY → CONDITIONALLY_READY
# THRESHOLD_NOT_READY – 1.00    → NOT_READY
READINESS_THRESHOLD_READY: float = 0.34
READINESS_THRESHOLD_NOT_READY: float = 0.66

# ── Hard-Rule Failure Risk Threshold ─────────────────────────────────────────
# If failure_risk exceeds this on a HIGH criticality component → NOT_READY
HARD_RULE_FAILURE_RISK_THRESHOLD: float = 0.75

# ── Maintenance Priority Weights ──────────────────────────────────────────────
# Priority = MW1×failure_risk + MW2×criticality + MW3×mission_impact + MW4×urgency
MAINTENANCE_W_FAILURE_RISK: float = 0.35
MAINTENANCE_W_CRITICALITY: float = 0.25
MAINTENANCE_W_MISSION_IMPACT: float = 0.25
MAINTENANCE_W_URGENCY: float = 0.15
