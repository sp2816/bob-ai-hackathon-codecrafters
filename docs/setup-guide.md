**# Setup Guide**

\> **\*\*This file is read by the automated evaluation pipeline. Be precise and complete.\*\***

**## Prerequisites**

Before you begin, ensure you have the following installed:

\- [ ] Python 3.11+

\- [ ] Node.js 18+

\- [ ] npm

\- [ ] Git

\- [ ] IBM Cloud account

\- [ ] IBM watsonx.ai project with an associated watsonx.ai Runtime service

\- [ ] IBM Bob, if you want to use the IBM Bob MCP integration

**## Environment Variables**

The core AssetSentinel application uses local synthetic data, trained machine learning artifacts, SQLite, and IBM watsonx.ai for the web copilot.

The application uses:

\- Synthetic sensor data

\- Local machine learning models

\- SQLite database

\- Locally stored model artifacts

\- IBM watsonx.ai for the web copilot

\- IBM Bob MCP integration for grounded IDE interaction

Create the environment file:

\`\`\`bash

cp src/.env.example src/.env

\`\`\`

The \`src/.env\` file must contain the required Watsonx configuration:

\`\`\`env

WATSONX_API_KEY=your_ibm_cloud_api_key

WATSONX_PROJECT_ID=your_watsonx_project_id

WATSONX_URL=https://<region>.ml.cloud.ibm.com

WATSONX_MODEL_ID=your_supported_model_id

DATABASE_URL=sqlite:///./asset_sentinel.db

APP_PORT=8000

APP_ENV=development

\`\`\`

### Watsonx Environment Variables

**\`WATSONX_API_KEY\`**

Your IBM Cloud API key used for programmatic authentication.

Create an API key from the IBM Cloud console under:

\`\`\`text

Manage

→

Access (IAM)

→

API keys

→

Create an IBM Cloud API key

\`\`\`

**\`WATSONX_PROJECT_ID\`**

The project ID of the IBM watsonx.ai project being used by the application.

**\`WATSONX_URL\`**

The regional IBM watsonx.ai Runtime endpoint.

Use the endpoint corresponding to the region where the watsonx.ai project is created.

Example:

\`\`\`text

https://eu-de.ml.cloud.ibm.com

\`\`\`

Do not use a different regional endpoint from the project unless the IBM watsonx.ai configuration explicitly supports it.

**\`WATSONX_MODEL_ID\`**

The ID of a foundation model supported by the selected watsonx.ai environment.

The model must be available in the project's region.

Do not assume that every IBM foundation model is available in every region.

### Important Credential Rule

Never commit the actual \`src/.env\` file to GitHub.

Each developer should use their own IBM Cloud API key and authorized Watsonx project credentials.

The repository should contain:

\`\`\`text

src/.env.example

\`\`\`

The repository should NOT contain:

\`\`\`text

src/.env

\`\`\`

If \`src/.env\` appears in \`git status\`, do not commit it.

Ensure that \`.gitignore\` contains:

\`\`\`text

.env

src/.env

\`\`\`

**## IBM watsonx.ai Project Setup**

Before starting the application, create or use an IBM watsonx.ai project.

The project must have an associated watsonx.ai Runtime service.

The basic setup is:

\`\`\`text

IBM Cloud

    ↓

watsonx.ai

    ↓

Create / Open Project

    ↓

Associate watsonx.ai Runtime

    ↓

Obtain Project ID

    ↓

Create IBM Cloud API Key

    ↓

Select Supported Foundation Model

    ↓

Configure src/.env
\`\`\`

The Watsonx project and Runtime service should be in a compatible region.

The selected model must be supported by the Watsonx environment.

**## Installation**

\`\`\`bash

# 1. Clone the repository

git clone https://github.com/sp2816/bob-ai-hackathon-codecrafters.git

# 2. Enter the project directory

cd bob-ai-hackathon-codecrafters

# 3. Create the Watsonx environment file

copy src\.env.example src\.env

# 4. Edit src/.env and enter your IBM Watsonx credentials

# 5. Install backend dependencies

pip install -r src/backend/member1_backend/requirements.txt

pip install -r src/backend/member2_ml/requirements.txt

# 6. Install frontend dependencies

cd src/frontend

npm install

# 7. Return to the project root

cd ../..

\`\`\`

On macOS/Linux, the environment-file command can be:

\`\`\`bash

cp src/.env.example src/.env

\`\`\`

On Windows PowerShell:

\`\`\`powershell

Copy-Item src\.env.example src\.env

\`\`\`

**## Database Setup**

The application uses SQLite with SQLAlchemy.

The database is local and does not require a separate PostgreSQL or MySQL server.

The backend initializes and accesses the SQLite database using the configured SQLAlchemy database URL.

The default configuration is:

\`\`\`text

DATABASE_URL=sqlite:///./asset_sentinel.db

\`\`\`

Ensure that the backend dependencies are installed before starting the application.

The application uses project data including:

\- Assets

\- Components

\- Sensor data

\- Predictions

\- Anomalies

\- Missions

\- Maintenance records

No separate PostgreSQL server is required for the core application.

**## Machine Learning Setup**

The Member 2 ML module uses trained model artifacts.

The ML pipeline includes:

\- Synthetic sensor data

\- Data loading and validation

\- Feature engineering

\- Random Forest failure prediction

\- Isolation Forest anomaly detection

\- Prediction service

The prediction service loads trained model artifacts during prediction.

Models are not retrained during normal prediction execution.

Verify that the required model artifacts and saved feature-column definitions are present in the expected Member 2 ML directories before running predictions.

**## IBM Bob MCP Setup**

IBM Bob integration is provided through the AssetSentinel MCP server.

The MCP server is implemented in:

\`\`\`text

src/backend/member1_backend/app/mcp_server.py

\`\`\`

The project-level IBM Bob configuration is:

\`\`\`text

.bob/mcp.json

\`\`\`

The MCP integration exposes read-only AssetSentinel tools.

The available tools include:

\`\`\`text

get_asset_status(asset_id)

get_asset_details(asset_id)

get_sensor_trends(asset_id)

get_component_health(asset_id)

get_failure_predictions(asset_id)

get_anomalies(asset_id)

get_maintenance_history(asset_id)

get_mission_readiness(asset_id, mission_id)

get_fleet_readiness()

get_maintenance_priorities()

get_mission_details(mission_id)

\`\`\`

IBM Bob connects to the local AssetSentinel MCP server using the project configuration.

The MCP server provides structured AssetSentinel information to IBM Bob.

The MCP tools are read-only.

They do not modify asset state, readiness decisions, maintenance records, or physical systems.

**## Running the Application**

The application requires the backend and frontend to run in separate terminals.

**### Start the Backend**

From the project root:

\`\`\`bash

cd src/backend/member1_backend

uvicorn app.main:app --reload

\`\`\`

The backend will typically run at:

\`\`\`text

http://localhost:8000

\`\`\`

You can access the FastAPI documentation at:

\`\`\`text

http://localhost:8000/docs

\`\`\`

The backend provides:

\- Asset APIs

\- Prediction APIs

\- Anomaly APIs

\- Readiness APIs

\- Maintenance APIs

\- Mission APIs

\- Copilot chat API

**### Start the Frontend**

Open a separate terminal.

From the project root:

\`\`\`bash

cd src/frontend

npm run dev

\`\`\`

The frontend will typically be available at:

\`\`\`text

http://localhost:5173

\`\`\`

The Vite development server may select another port if port 5173 is already in use.

**## Running Tests**

From the project root, run the backend test suite:

\`\`\`bash

pytest src/backend -v

\`\`\`

To run only the Member 2 Machine Learning tests:

\`\`\`bash

pytest src/backend/member2_ml/tests -v

\`\`\`

The Member 2 ML tests verify:

\- Synthetic data generation

\- Data loading and validation

\- Feature engineering

\- Random Forest training and inference

\- Isolation Forest anomaly detection

\- Prediction service

\- Contract-compliant prediction output

\- Model artifact loading

\- No model retraining during prediction

The backend tests also validate backend functionality and integration.

**## Quick Demo**

**### 1. Configure Watsonx**

Create:

\`\`\`text

src/.env

\`\`\`

and configure:

\`\`\`env

WATSONX_API_KEY=your_ibm_cloud_api_key

WATSONX_PROJECT_ID=your_watsonx_project_id

WATSONX_URL=https://<region>.ml.cloud.ibm.com

WATSONX_MODEL_ID=your_supported_model_id

DATABASE_URL=sqlite:///./asset_sentinel.db

APP_PORT=8000

APP_ENV=development

\`\`\`

**### 2. Start the Backend**

\`\`\`bash

cd src/backend/member1_backend

uvicorn app.main:app --reload

\`\`\`

**### 3. Start the Frontend**

In a separate terminal:

\`\`\`bash

cd src/frontend

npm run dev

\`\`\`

**### 4. Open the Application**

Open the frontend URL shown by Vite, typically:

\`\`\`text

http://localhost:5173

\`\`\`

**### 5. View Predictions**

The backend exposes prediction APIs including:

\`\`\`text

GET /predictions/

\`\`\`

Get predictions for a specific asset:

\`\`\`text

GET /predictions/asset/{id}

\`\`\`

Get anomaly results:

\`\`\`text

GET /predictions/anomalies

\`\`\`

Get anomaly results for a specific asset:

\`\`\`text

GET /predictions/anomalies/asset/{id}

\`\`\`

Example:

\`\`\`text

GET /predictions/asset/AS-1047

\`\`\`

The prediction pipeline provides:

\- Failure probability

\- Risk category

\- Anomaly score

\- Anomaly status

\- Anomaly severity

\- Affected sensor

\- Timestamp

The ML pipeline uses:

\- Random Forest for failure probability and risk category

\- Isolation Forest for anomaly detection and anomaly severity

**### 6. Test the Web Copilot**

Open the Copilot page in the AssetSentinel frontend.

Example questions:

\`\`\`text

What is the status of AS-1047?

Why is AS-1047 not ready?

Which component has the highest failure risk on AS-1047?

What anomalies were detected on AS-1047?

Show the maintenance history for AS-1047.

What is the current fleet readiness?

Which assets need immediate attention?

What are today's maintenance priorities?

Is AS-1047 ready for MSN-001?
\`\`\`

The web copilot sends the question through:

\`\`\`text

React

    ↓

FastAPI

    ↓

chat_service.py

    ↓

watsonx_service.py

    ↓

IBM watsonx.ai

    ↓

Shared Copilot Tools

    ↓

Live AssetSentinel Data

    ↓

IBM watsonx.ai

    ↓

Grounded Response

    ↓

React
\`\`\`

The copilot must use live AssetSentinel data for factual questions.

It must not fabricate project information.

**### 7. Test a Nonexistent Asset**

Ask:

\`\`\`text

What is the status of AS-FAKE-999?
\`\`\`

The system should report that the asset was not found rather than inventing a status.

Expected behavior:

\`\`\`text

The asset AS-FAKE-999 was not found in the system.
Please verify the asset ID and try again.
\`\`\`

This validates that the copilot is grounded in the AssetSentinel data.

**### 8. Test IBM Bob MCP**

Open the AssetSentinel project in IBM Bob.

Verify that:

\`\`\`text

.bob/mcp.json
\`\`\`

is present.

Start or enable the AssetSentinel MCP server.

Confirm that IBM Bob can discover the AssetSentinel tools.

Test a read-only tool such as:

\`\`\`text

get_asset_status("AS-1047")
\`\`\`

Verify that the result corresponds to actual AssetSentinel data.

The IBM Bob integration flow is:

\`\`\`text

IBM Bob

    ↓

MCP

    ↓

AssetSentinel MCP Server

    ↓

Shared Copilot Tools

    ↓

Live AssetSentinel Data

    ↓

IBM Bob Explanation
\`\`\`

**## Architecture Overview**

The main application flow is:

\`\`\`text

Synthetic Sensor Data

        ↓

Data Loading & Validation

        ↓

Feature Engineering

        ↓

Random Forest + Isolation Forest

        ↓

Predictions + Anomalies

        ↓

Backend Integration

        ↓

Evidence Layer

        ↓

Readiness Engine

        ↓

Maintenance Priority Engine

        ↓

FastAPI APIs

        ↓

React Frontend
\`\`\`

The web AI flow is:

\`\`\`text

React Copilot

        ↓

FastAPI

        ↓

IBM watsonx.ai

        ↓

Shared Copilot Tools

        ↓

Live AssetSentinel Data

        ↓

Grounded AI Explanation
\`\`\`

The IBM Bob integration flow is:

\`\`\`text

IBM Bob

        ↓

MCP

        ↓

AssetSentinel MCP Server

        ↓

Shared Copilot Tools

        ↓

Live AssetSentinel Data

        ↓

IBM Bob Explanation
\`\`\`

The architectural principle is:

\`\`\`text

ML detects → Evidence proves → Readiness Engine decides

→ Maintenance Engine prioritizes → IBM AI explains
\`\`\`

IBM watsonx.ai powers the web copilot.

IBM Bob connects to AssetSentinel through MCP.

Neither AI integration overrides the Readiness Engine.

**## Important AI Boundary**

The AssetSentinel website does not embed the IBM Bob IDE itself.

Instead:

\`\`\`text

Web Application → IBM watsonx.ai

IBM Bob IDE → AssetSentinel MCP Server
\`\`\`

This provides two genuine IBM integrations with clearly separated responsibilities.

The Readiness Engine remains the authority for readiness decisions.

**## Troubleshooting**

\| Issue | Solution |
\|---|---|
\| \`ModuleNotFoundError\` | Install backend dependencies using the appropriate \`requirements.txt\` files |
\| \`pytest\` command not found | Install pytest using \`pip install pytest\` |
\| Frontend dependencies missing | Run \`npm install\` inside \`src/frontend\` |
\| Backend does not start | Verify backend dependencies are installed and run Uvicorn from \`src/backend/member1_backend\` |
\| Port 8000 already in use | Stop the existing process using port 8000 or run Uvicorn on another port |
\| Port 5173 already in use | Stop the existing process or allow Vite to select another available port |
\| ML artifact not found | Verify that trained model artifact files exist in the expected Member 2 ML artifact directory |
\| ML prediction fails | Run \`pytest src/backend/member2_ml/tests -v\` to verify the ML pipeline |
\| Database errors | Verify the SQLite database path and SQLAlchemy configuration |
\| API endpoint not responding | Confirm the FastAPI backend is running on the expected port |
\| Frontend cannot connect to backend | Verify the backend URL and CORS configuration |
\| Prediction API returns no data | Verify database initialization, seed data, and ML/backend integration have completed |
\| Git merge conflicts | Resolve conflicts manually, then run \`git add .\` followed by \`git commit\` |
\| Import error for Member 2 ML | Verify Python paths and ensure \`member2_ml\` is available to the backend environment |
\| Random Forest prediction fails | Verify the saved Random Forest model artifacts and feature columns are available |
\| Isolation Forest prediction fails | Verify the saved Isolation Forest model artifacts and feature columns are available |
\| Watsonx API key error | Verify \`WATSONX_API_KEY\` is a valid IBM Cloud API key and has access to the Watsonx project |
\| Watsonx project error | Verify \`WATSONX_PROJECT_ID\` belongs to the configured IBM watsonx.ai project |
\| Watsonx Runtime error | Verify that the watsonx.ai Runtime service is associated with the project |
\| Watsonx model unavailable | Verify that \`WATSONX_MODEL_ID\` is supported in the project's region |
\| Watsonx regional error | Verify that \`WATSONX_URL\` matches the region of the Watsonx project |
\| Watsonx chat request fails | Check backend logs for the actual IBM watsonx.ai API response and verify credentials, project, runtime, and model configuration |
\| Copilot returns no useful answer | Verify that Watsonx is configured correctly and that the shared AssetSentinel tools can access the database |
\| Copilot invents project data | Verify that the Watsonx tool-calling integration is enabled and that factual questions are routed through the shared tools |
\| Unknown asset query | Verify the asset ID; the copilot should explicitly report when an asset does not exist |
\| MCP server does not start | Verify MCP dependencies and run the MCP server from the correct project environment |
\| IBM Bob cannot discover MCP tools | Verify that \`.bob/mcp.json\` exists and points to the correct AssetSentinel MCP server |
\| IBM Bob MCP connection fails | Verify that the MCP server is running and that the configured transport and command are correct |
\| MCP tool returns no data | Verify database initialization and the shared copilot tool implementation |
\| MCP tool modifies data | MCP tools are intended to be read-only; verify the MCP server implementation and tool definitions |
\| \`src/.env\` is missing | Copy \`src/.env.example\` to \`src/.env\` and configure the required Watsonx values |
\| \`src/.env\` encoding error | Recreate the file as UTF-8 plain text and ensure it is not saved as UTF-16 |
\| API key committed accidentally | Remove the secret from the repository history if necessary, revoke/rotate the exposed IBM Cloud API key, and add \`src/.env\` to \`.gitignore\` |
\| Team member Watsonx setup fails | Each team member should configure their own local IBM Cloud API key and authorized Watsonx project credentials |