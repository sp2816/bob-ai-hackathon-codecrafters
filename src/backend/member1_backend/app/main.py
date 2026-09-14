import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
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
)
from app.services.watsonx_service import validate_watsonx_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create all DB tables on startup

Base.metadata.create_all(bind=engine)

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


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
