import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, SessionLocal
import logging
from app.routers import (
    assets,
    components,
    sensor_data,
    maintenance,
    maintenance_records,
    missions,
    fleet,
    predictions,
    notifications,
    chat,
    cost_assumptions,
)
from app.services.watsonx_service import validate_watsonx_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.models.cost_assumption import CostAssumption

# Create all DB tables on startup (does not alter existing tables)
Base.metadata.create_all(bind=engine)

# Safe SQLite Schema Migration for missing columns
try:
    from sqlalchemy import text
    with engine.begin() as conn:
        result = conn.execute(text("PRAGMA table_info(cost_assumptions)"))
        existing_columns = [row[1] for row in result]
        
        missing_cols = {
            "monitoring_cost_traditional": "FLOAT DEFAULT 500.0",
            "inspection_cost_traditional": "FLOAT DEFAULT 10000.0",
            "preventive_maintenance_traditional": "FLOAT DEFAULT 12000.0",
            "sensor_data_cost_assetsentinel": "FLOAT DEFAULT 750.0",
            "assetsentinel_deployment_cost": "FLOAT DEFAULT 100000.0",
            "residual_failure_probability_multiplier": "FLOAT DEFAULT 0.10"
        }
        
        for col_name, col_def in missing_cols.items():
            if col_name not in existing_columns:
                logger.info(f"Migrating schema: Adding {col_name} to cost_assumptions")
                conn.execute(text(f"ALTER TABLE cost_assumptions ADD COLUMN {col_name} {col_def}"))
                
        # Also update existing rows for columns that might be 0.0 from an incomplete previous migration
        conn.execute(text("""
            UPDATE cost_assumptions
            SET 
                emergency_intervention_cost = repair_cost * 2 WHERE emergency_intervention_cost = 0 OR emergency_intervention_cost IS NULL;
        """))
        conn.execute(text("""
            UPDATE cost_assumptions
            SET 
                emergency_maintenance_cost = replacement_cost * 1.5 WHERE emergency_maintenance_cost = 0 OR emergency_maintenance_cost IS NULL;
        """))
        conn.execute(text("""
            UPDATE cost_assumptions
            SET 
                downtime_cost_per_hour = 5000.0 WHERE downtime_cost_per_hour = 0 OR downtime_cost_per_hour IS NULL;
        """))
        conn.execute(text("""
            UPDATE cost_assumptions
            SET 
                planned_downtime_hours = 8.0 WHERE planned_downtime_hours = 0 OR planned_downtime_hours IS NULL;
        """))
        conn.execute(text("""
            UPDATE cost_assumptions
            SET 
                emergency_downtime_hours = 48.0 WHERE emergency_downtime_hours = 0 OR emergency_downtime_hours IS NULL;
        """))
        conn.execute(text("""
            UPDATE cost_assumptions
            SET 
                mission_disruption_cost = failure_impact_cost * 0.5 WHERE mission_disruption_cost = 0 OR mission_disruption_cost IS NULL;
        """))
except Exception as e:
    logger.error(f"Migration error: {e}")

app = FastAPI(
    title="AssetSentinel — Member 1 Backend",
    description=(
        "Core backend API: assets, components, sensor data, "
        "maintenance records, missions, and fleet overview."
    ),
    version="1.0.0",
)

@app.on_event("startup")
def startup_event():
    config_status = validate_watsonx_config()
    logger.info("=== AssetSentinel Startup Audit ===")
    logger.info(f"Watsonx API Key configured: {'yes' if config_status['watsonx_configured'] else 'no'}")
    logger.info(f"Watsonx Project ID configured: {'yes' if config_status['project_configured'] else 'no'}")
    logger.info(f"Watsonx Model ID configured: {'yes' if config_status['model_configured'] else 'no'}")
    logger.info("===================================")

    # Seed Cost Assumptions
    db = SessionLocal()
    try:
        if db.query(CostAssumption).count() == 0:
            logger.info("Seeding default Modeled Demo Cost Assumptions...")
            def _make_cost(comp: str, insp: float, rep: float, repl: float, impact: float):
                # Generic base values
                monitoring_trad = 500.0
                return CostAssumption(
                    component_type=comp,
                    inspection_cost=insp,
                    repair_cost=rep,
                    replacement_cost=repl,
                    failure_impact_cost=impact,
                    monitoring_cost_traditional=monitoring_trad,
                    inspection_cost_traditional=insp,
                    preventive_maintenance_traditional=rep * 0.1,  # arbitrary 10% of repair cost
                    sensor_data_cost_assetsentinel=monitoring_trad * 1.5, # distinctly different from traditional
                    assetsentinel_deployment_cost=100000.0, # 100k per asset deployment cost assumption
                    residual_failure_probability_multiplier=0.10,
                    emergency_intervention_cost=rep * 2,
                    emergency_maintenance_cost=repl * 1.5,
                    downtime_cost_per_hour=5000.0,
                    planned_downtime_hours=8.0,
                    emergency_downtime_hours=48.0,
                    mission_disruption_cost=impact * 0.5
                )
                
            defaults = [
                _make_cost("main_bearing", 10000, 120000, 500000, 899000),
                _make_cost("engine", 20000, 300000, 1500000, 2500000),
                _make_cost("hydraulics", 5000, 80000, 250000, 400000),
                _make_cost("avionics", 15000, 150000, 800000, 1200000),
                _make_cost("landing_gear", 12000, 200000, 700000, 1000000),
            ]
            db.add_all(defaults)
            db.commit()
    finally:
        db.close()

# ---------------------------------------------------------------------------
# CORS — allow the React frontend (Vite default port 5173) and any override
# ---------------------------------------------------------------------------
_raw_origins = os.environ.get(
    "ASSETSENTINEL_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

app.include_router(assets.router)
app.include_router(components.router)
app.include_router(sensor_data.router)
app.include_router(maintenance.router)
app.include_router(maintenance_records.router)
app.include_router(missions.router)
app.include_router(fleet.router)
app.include_router(predictions.router)
app.include_router(notifications.router)
app.include_router(chat.router)
app.include_router(cost_assumptions.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
