# IBM Bob & Watsonx.ai Integration Architecture

This document outlines the genuine IBM AI integration architecture used in the AssetSentinel project.

## Overview
AssetSentinel utilizes a dual-path integration strategy to provide grounded, real-time AI capabilities both within the web application and directly inside the developer's IDE.

1. **Website Chatbot**: Powered by a real IBM **watsonx.ai** Large Language Model (LLM) utilizing `langchain-ibm` for tool calling and grounded context retrieval.
2. **Developer IDE**: Powered by **IBM Bob** through a standard Model Context Protocol (MCP) server.

Both systems query the **exact same underlying SQLite database** using a shared `copilot_tools.py` toolset. This ensures consistency between what an operator sees in the chatbot and what a developer sees in the IDE.

## 1. Website Chatbot Integration (Watsonx.ai)
The React frontend chatbot delegates all intelligence to the backend `POST /chat` endpoint. The backend implements a robust Watsonx.ai chain that replaces all hardcoded, regex-based intent matching.

### Data Flow
1. User types a question in the React UI.
2. `POST /chat` routes to `watsonx_service.py`.
3. The Watsonx model determines which data is required and issues tool calls.
4. Tools (e.g., `get_failure_predictions(asset_id)`) fetch live SQLite data.
5. The LLM generates a grounded natural language response based exclusively on the retrieved facts.

### Setup Instructions
To enable the website chatbot, copy `.env.example` to `.env` in `src/` and populate your Watsonx credentials:
```env
WATSONX_API_KEY=your_ibm_cloud_api_key
WATSONX_PROJECT_ID=your_watsonx_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-13b-chat-v2
```
*Note: If credentials are not configured, the backend will gracefully degrade and inform the user to configure them, without crashing.*

## 2. IBM Bob IDE Integration (MCP Server)
IBM Bob itself is an IDE-based coding assistant and does not provide an external web embedding API. To allow developers to interact with AssetSentinel's live operational data from within their IDE, we provide a standard MCP server.

### Data Flow
1. Developer asks a question in the IBM Bob IDE Chat.
2. IBM Bob invokes tools via the `mcp_server.py` stdio interface.
3. `mcp_server.py` executes the shared `copilot_tools.py` database queries.
4. Results are serialized as JSON and returned to IBM Bob.

### Setup Instructions
The MCP server is configured in `.bob/mcp.json`:
```json
{
  "mcpServers": {
    "AssetSentinel": {
      "command": "python",
      "args": ["-m", "app.mcp_server"],
      "cwd": "${workspaceFolder}/src/backend/member1_backend"
    }
  }
}
```
Simply start the IBM Bob client in your IDE; it will automatically spin up the MCP server and register the 11 read-only data tools.
