import os
import json
import logging
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv

# Define strict .env path (src/.env)
ENV_PATH = Path(__file__).resolve().parents[4] / '.env'
load_dotenv(dotenv_path=ENV_PATH)


from langchain_ibm import ChatWatsonx
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

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

def get_db():
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise

@tool
def get_asset_status(asset_id: str) -> str:
    """Returns the status, metadata, and latest readiness result for an asset. Requires asset_id."""
    db = get_db()
    try:
        return get_asset_status_tool(db, asset_id)
    finally:
        db.close()

@tool
def get_asset_details(asset_id: str) -> str:
    """Returns detailed asset information including components, criticality, and operational hours. Requires asset_id."""
    db = get_db()
    try:
        return get_asset_details_tool(db, asset_id)
    finally:
        db.close()

@tool
def get_sensor_trends(asset_id: str) -> str:
    """Returns recent sensor readings and trend information for an asset. Requires asset_id."""
    db = get_db()
    try:
        return get_sensor_trends_tool(db, asset_id)
    finally:
        db.close()

@tool
def get_component_health(asset_id: str) -> str:
    """Returns component health and service hours for all components in an asset. Requires asset_id."""
    db = get_db()
    try:
        return get_component_health_tool(db, asset_id)
    finally:
        db.close()

@tool
def get_failure_predictions(asset_id: str) -> str:
    """Returns component failure predictions, probability, and risk level. Requires asset_id."""
    db = get_db()
    try:
        return get_failure_predictions_tool(db, asset_id)
    finally:
        db.close()

@tool
def get_anomalies(asset_id: str) -> str:
    """Returns recent sensor anomalies, severity, and scores. Requires asset_id."""
    db = get_db()
    try:
        return get_anomalies_tool(db, asset_id)
    finally:
        db.close()

@tool
def get_maintenance_history(asset_id: str) -> str:
    """Returns service records, inspection status, and overdue status. Requires asset_id."""
    db = get_db()
    try:
        return get_maintenance_history_tool(db, asset_id)
    finally:
        db.close()

@tool
def get_mission_readiness(asset_id: str, mission_id: str) -> str:
    """Returns readiness status, score, reasons, and evidence for a specific mission."""
    db = get_db()
    try:
        return get_mission_readiness_tool(db, asset_id, mission_id)
    finally:
        db.close()

@tool
def get_fleet_readiness() -> str:
    """Returns fleet summary, ready count, conditional count, and not ready count."""
    db = get_db()
    try:
        return get_fleet_readiness_tool(db)
    finally:
        db.close()

@tool
def get_maintenance_priorities() -> str:
    """Returns ranked maintenance recommendations, urgency, priority score, and actions."""
    db = get_db()
    try:
        return get_maintenance_priorities_tool(db)
    finally:
        db.close()

@tool
def get_mission_details(mission_id: str) -> str:
    """Returns mission requirements, criticality, and relevant thresholds."""
    db = get_db()
    try:
        return get_mission_details_tool(db, mission_id)
    finally:
        db.close()

tools_list = [
    get_asset_status,
    get_asset_details,
    get_sensor_trends,
    get_component_health,
    get_failure_predictions,
    get_anomalies,
    get_maintenance_history,
    get_mission_readiness,
    get_fleet_readiness,
    get_maintenance_priorities,
    get_mission_details
]

tools_by_name = {t.name: t for t in tools_list}

SYSTEM_PROMPT = """You are the AssetSentinel Mission Readiness Copilot, an AI maintenance and mission readiness copilot for military and high-value operational assets.

You help operators:
1. Identify non-ready assets.
2. Explain why assets are not ready.
3. Analyze readiness evidence.
4. Identify components likely to fail.
5. Explain failure probabilities.
6. Detect critical anomalies.
7. Explain anomaly severity.
8. Analyze sensor trends.
9. Review maintenance history.
10. Recommend prioritized maintenance.
11. Explain maintenance priority.
12. Evaluate mission readiness.
13. Summarize fleet operational risk.
14. Compare asset conditions.
15. Identify assets requiring immediate attention.

RULES:
- You MUST use tools to retrieve factual project data.
- NEVER invent asset status, prediction values, anomalies, maintenance recommendations, or readiness scores.
- Clearly state when data is unavailable (e.g. "I could not find prediction data for that asset.").
- Explain reasoning based on retrieved evidence.
- Be concise but informative.
- Mention asset IDs and component IDs when relevant.
"""

_chat_history = []
_llm_instance = None

def validate_watsonx_config() -> Dict[str, bool]:
    """Safely validate configuration without exposing secrets."""
    return {
        "watsonx_configured": bool(os.getenv("WATSONX_API_KEY") and os.getenv("WATSONX_API_KEY") not in ("your_api_key_here", "your_ibm_cloud_api_key")),
        "project_configured": bool(os.getenv("WATSONX_PROJECT_ID") and os.getenv("WATSONX_PROJECT_ID") != "your_project_id_here"),
        "model_configured": bool(os.getenv("WATSONX_MODEL_ID"))
    }

def get_llm():
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    config_status = validate_watsonx_config()
    if not all(config_status.values()):
        return None

    api_key = os.getenv("WATSONX_API_KEY")
    project_id = os.getenv("WATSONX_PROJECT_ID")
    url = os.getenv("WATSONX_URL")
    model_id = os.getenv("WATSONX_MODEL_ID")

    try:
        llm = ChatWatsonx(
            model_id=model_id,
            url=url,
            project_id=project_id,
            apikey=api_key,
            params={
                "max_new_tokens": 512,
                "temperature": 0.0,
            }
        )
        _llm_instance = llm.bind_tools(tools_list)
        return _llm_instance
    except Exception as e:
        logging.error(f"Error initializing Watsonx: {e}")
        return None

def clean_response_content(content) -> str:
    """
    Clean only invalid rendering artifacts from the IBM AI response.
    Does not change the AI's actual response style or wording.
    """

    if content is None:
        return ""

    # Handle content returned as a list
    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if text:
                    parts.append(str(text))
            else:
                parts.append(str(item))

        content = "\n".join(parts)

    content = str(content).strip()

    # Remove only standalone unwanted rendering artifacts
    invalid_artifacts = [
        "svg",
        "**svg**",
        "`svg`",
        "```svg",
        "```"
    ]

    # If the entire response is just an artifact, return empty
    if content.lower().strip() in [
        "svg",
        "**svg**",
        "`svg`"
    ]:
        return ""

    # Remove a leading svg artifact only
    lines = content.splitlines()

    while lines and lines[0].strip().lower() in [
        "svg",
        "**svg**",
        "`svg`",
        "```svg"
    ]:
        lines.pop(0)

    return "\n".join(lines).strip()

def process_message_with_watsonx(message: str) -> str:
    llm = get_llm()
    if not llm:
        return "IBM AI service is not configured. Please configure watsonx.ai credentials."


    try:
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + _chat_history + [HumanMessage(content=message)]
        
        response = llm.invoke(messages)
        
        _chat_history.append(HumanMessage(content=message))
        
        # Tool call loops
        # To handle multiple sequential tool calls safely, we can do a simple loop (up to 3 times)
        iterations = 0
        while hasattr(response, 'tool_calls') and response.tool_calls and iterations < 3:
            _chat_history.append(response)
            
            tool_messages = []
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                try:
                    tool_instance = tools_by_name[tool_name]
                    tool_result = tool_instance.invoke(tool_args)
                    tool_messages.append(ToolMessage(tool_call_id=tool_call["id"], content=str(tool_result)))
                except Exception as e:
                    tool_messages.append(ToolMessage(tool_call_id=tool_call["id"], content=f"Error executing {tool_name}: {e}"))
            
            _chat_history.extend(tool_messages)
            
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + _chat_history
            response = llm.invoke(messages)
            iterations += 1
            
        _chat_history.append(response)

        if len(_chat_history) > 10:
            _chat_history[:] = _chat_history[-10:]

        final_response = clean_response_content(response.content)

        # Prevent blank chatbot bubbles
        if not final_response:
            logging.warning(
                f"Watsonx returned empty response content: {response.content}"
            )

            return (
                "I retrieved the available information, but I was unable to "
                "generate a complete response. Please try asking again."
            )

        return final_response

    except Exception as e:
        print(f"Watsonx API error: {e}")
        return "The AI service is temporarily unavailable. Please try again."
