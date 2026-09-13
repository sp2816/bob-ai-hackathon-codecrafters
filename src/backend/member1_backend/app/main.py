from fastapi import FastAPI
from app.database import engine, Base
from app.routers import (
    assets,
    components,
    sensor_data,
    maintenance,
    maintenance_records,
    missions,
    fleet,
)

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

app.include_router(assets.router)
app.include_router(components.router)
app.include_router(sensor_data.router)
app.include_router(maintenance.router)
app.include_router(maintenance_records.router)
app.include_router(missions.router)
app.include_router(fleet.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
