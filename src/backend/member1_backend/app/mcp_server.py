from mcp.server.mcpserver import MCPServer
from app.database import SessionLocal
from app.services.copilot_tools import (
    get_asset_status_tool,
    get_asset_details_tool,
    get_sensor_trends_tool,
    get_component_health_tool,
    get_failure_predictions_tool,
    get_anomalies_tool,
    get_maintenance_history_tool,
    get_mission_readiness_tool,
    get_fleet_readiness_tool,
    get_maintenance_priorities_tool,
    get_mission_details_tool
)

mcp = MCPServer("AssetSentinel")

def get_db():
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise

@mcp.tool()
def get_asset_status(asset_id: str) -> str:
    """Returns the status, metadata, and latest readiness result for an asset."""
    db = get_db()
    try:
        return get_asset_status_tool(db, asset_id)
    finally:
        db.close()

@mcp.tool()
def get_asset_details(asset_id: str) -> str:
    """Returns detailed asset information including components, criticality, and operational hours."""
    db = get_db()
    try:
        return get_asset_details_tool(db, asset_id)
    finally:
        db.close()

@mcp.tool()
def get_sensor_trends(asset_id: str) -> str:
    """Returns recent sensor readings and trend information for an asset."""
    db = get_db()
    try:
        return get_sensor_trends_tool(db, asset_id)
    finally:
        db.close()

@mcp.tool()
def get_component_health(asset_id: str) -> str:
    """Returns component health and service hours for all components in an asset."""
    db = get_db()
    try:
        return get_component_health_tool(db, asset_id)
    finally:
        db.close()

@mcp.tool()
def get_failure_predictions(asset_id: str) -> str:
    """Returns component failure predictions, probability, and risk level."""
    db = get_db()
    try:
        return get_failure_predictions_tool(db, asset_id)
    finally:
        db.close()

@mcp.tool()
def get_anomalies(asset_id: str) -> str:
    """Returns recent sensor anomalies, severity, and scores."""
    db = get_db()
    try:
        return get_anomalies_tool(db, asset_id)
    finally:
        db.close()

@mcp.tool()
def get_maintenance_history(asset_id: str) -> str:
    """Returns service records, inspection status, and overdue status."""
    db = get_db()
    try:
        return get_maintenance_history_tool(db, asset_id)
    finally:
        db.close()

@mcp.tool()
def get_mission_readiness(asset_id: str, mission_id: str) -> str:
    """Returns readiness status, score, reasons, and evidence for a specific mission."""
    db = get_db()
    try:
        return get_mission_readiness_tool(db, asset_id, mission_id)
    finally:
        db.close()

@mcp.tool()
def get_fleet_readiness() -> str:
    """Returns fleet summary, ready count, conditional count, and not ready count."""
    db = get_db()
    try:
        return get_fleet_readiness_tool(db)
    finally:
        db.close()

@mcp.tool()
def get_maintenance_priorities() -> str:
    """Returns ranked maintenance recommendations, urgency, priority score, and actions."""
    db = get_db()
    try:
        return get_maintenance_priorities_tool(db)
    finally:
        db.close()

@mcp.tool()
def get_mission_details(mission_id: str) -> str:
    """Returns mission requirements, criticality, and relevant thresholds."""
    db = get_db()
    try:
        return get_mission_details_tool(db, mission_id)
    finally:
        db.close()

if __name__ == "__main__":
    # Start the MCPServer on stdio
    mcp.run()
