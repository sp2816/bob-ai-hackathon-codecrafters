**# AssetSentinel — Architecture**

**\*\*Mission Readiness & Predictive Maintenance Copilot\*\***

Team: Codecrafters | IBM Bob AI Hackathon

\---

**## System Architecture**

\`\`\`mermaid
flowchart TD

    User["👤 Human Operator"]

    React["React Frontend

    Dashboard / Assets / Missions

    Predictions / Maintenance / Readiness

    Copilot"]

    FastAPI["FastAPI Backend

    API Layer"]

    DB["SQLite + SQLAlchemy

    Assets, Components, Sensor Data

    Predictions, Anomalies

    Missions, Maintenance Records"]

    CSV["Synthetic Sensor Data

    CSV Files"]

    DL["Data Loading & Validation"]

    FE["Feature Engineering

    Rolling Statistics

    Trend Slopes

    Z-Scores"]

    RF["Random Forest

    Failure Probability

    Risk Category"]

    IF["Isolation Forest

    Anomaly Score

    Status / Severity"]

    ML["Member 2 ML

    Prediction Service

    Contract-Compliant Output"]

    EL["Evidence Layer

    Canonical Evidence Object"]

    RE["Readiness Engine

    Hard Rules + Score

    READY / CONDITIONALLY READY / NOT READY"]

    ME["Maintenance Engine

    Ranked Maintenance Actions"]

    Tools["Shared Copilot Tools

    Live DB-Backed Functions"]

    Watson["IBM watsonx.ai

    Web Copilot LLM"]

    MCP["AssetSentinel MCP Server

    11 Read-Only Tools"]

    Bob["IBM Bob IDE

    MCP Host / Development Copilot"]

    User -->|"View dashboard"| React

    React -->|"REST API"| FastAPI

    FastAPI --> DB

    CSV --> DL

    DL --> FE

    FE --> RF

    FE --> IF

    RF --> ML

    IF --> ML

    ML -->|"Predictions + Anomalies"| FastAPI

    FastAPI --> EL

    DB -->|"Maintenance + Mission Data"| EL

    EL -->|"Evidence Object"| RE

    EL -->|"Evidence Object"| ME

    RE -->|"Readiness Results"| DB

    ME -->|"Maintenance Recommendations"| DB

    FastAPI -->|"Readiness Data"| React

    FastAPI -->|"Prediction Data"| React

    FastAPI -->|"Maintenance Data"| React

    React -->|"Chat Request"| FastAPI

    FastAPI -->|"Grounded Query"| Watson

    Watson -->|"Tool Calls"| Tools

    Tools -->|"Live Database Results"| Watson

    Watson -->|"Grounded Explanation"| FastAPI

    FastAPI -->|"Chat Response"| React

    Bob -->|"MCP Protocol"| MCP

    MCP -->|"Calls Shared Tools"| Tools

    Tools -->|"Structured Results"| MCP

    MCP -->|"Grounded Data"| Bob

    style ML fill:#8e44ad,stroke:#5b2c6f,color:#fff

    style EL fill:#f4d03f,stroke:#d4ac0d,color:#000

    style RE fill:#e74c3c,stroke:#c0392b,color:#fff

    style Watson fill:#2e86c1,stroke:#1a5276,color:#fff

    style MCP fill:#2e86c1,stroke:#1a5276,color:#fff

    style Bob fill:#2e86c1,stroke:#1a5276,color:#fff
\`\`\`

\---

**## Core Principle**

\`\`\`text
ML detects

    ↓

Evidence combines context

    ↓

Readiness Engine decides

    ↓

Maintenance Engine prioritizes

    ↓

IBM AI explains
\`\`\`

**\*\*The Readiness Engine is the authority for readiness decisions.\*\***

**\*\*IBM watsonx.ai and IBM Bob NEVER override the Readiness Engine.\*\***

**\*\*React NEVER calculates readiness. It renders backend-computed results.\*\***

**\*\*Member 2 ML NEVER calculates readiness, mission scores, RUL, or maintenance recommendations.\*\***

\---

**# Module Responsibilities**

**## Member 1 — Backend**

Responsible for:

\- FastAPI APIs

\- Database integration

\- SQLAlchemy models

\- Pydantic schemas

\- Prediction and anomaly APIs

\- Runtime integration between modules

\- Chat API integration

\- IBM watsonx.ai integration

\- MCP server integration

Member 1 exposes APIs for prediction data such as:

\`\`\`text
GET /predictions/

GET /predictions/asset/{id}

GET /predictions/anomalies

GET /predictions/anomalies/asset/{id}
\`\`\`

The backend is responsible for providing authoritative AssetSentinel data to the frontend and AI integration layers.

\---

**## Member 2 — Machine Learning**

Responsible for:

\- Synthetic sensor data

\- Data loading and validation

\- Feature engineering

\- Random Forest failure prediction

\- Isolation Forest anomaly detection

\- ML prediction service

Member 2 provides:

**### Random Forest Output**

\`\`\`text
prediction_id

asset_id

component_id

failure_probability

risk_category

timestamp
\`\`\`

**### Isolation Forest Output**

\`\`\`text
asset_id

component_id

anomaly_score

anomaly_status

anomaly_severity

sensor

timestamp
\`\`\`

Member 2 uses real trained model artifacts.

Models are loaded during prediction.

Models are NOT retrained during prediction.

Member 2 does NOT implement:

\- FastAPI

\- Database logic

\- Evidence Layer

\- Readiness scoring

\- Mission evaluation

\- Maintenance recommendations

\- RUL

\- Frontend logic

\- Copilot reasoning

\---

**## Member 3 — Evidence and Readiness**

Responsible for:

\- Evidence Layer

\- Canonical Evidence Object

\- Readiness evaluation

\- Maintenance prioritization

\- Mission-related decisions

Member 3 consumes ML output as evidence.

The Evidence Layer combines:

\- Failure probability

\- Risk category

\- Anomaly score

\- Anomaly status

\- Anomaly severity

\- Sensor

\- Maintenance information

\- Component criticality

\- Mission information

The ML output itself is not modified or recalculated.

\---

**## Frontend**

Responsible for:

\- Dashboard

\- Asset views

\- Prediction views

\- Anomaly views

\- Maintenance views

\- Readiness views

\- Mission views

\- Copilot interface

The frontend consumes backend APIs.

The frontend does NOT calculate:

\- ML predictions

\- Readiness scores

\- Maintenance priorities

\- Failure probabilities

\- Anomaly scores

The frontend renders values computed by the backend and ML modules.

\---

**# Machine Learning Architecture**

\`\`\`text
Synthetic / Sensor Data

        │

        ▼

Data Loading & Validation

        │

        ▼

Feature Engineering

        │

        ├───────────────────────┐

        │                       │

        ▼                       ▼

Random Forest             Isolation Forest

Failure Prediction        Anomaly Detection

        │                       │

        │                       │

        └───────────┬───────────┘

                    │

                    ▼

            ML Prediction Service

                    │

                    ▼

          Contract-Compliant Output

                    │

                    ▼

                 Backend
\`\`\`

\---

**# Feature Engineering**

The ML pipeline transforms raw sensor readings into meaningful historical behavior features.

Sensors include:

\- Vibration

\- Temperature

\- Pressure

\- RPM

Engineered behavior indicators can include:

\- Latest value

\- Rolling mean

\- Rolling standard deviation

\- Maximum value

\- Trend slope

\- Maximum z-score

These features allow the models to analyze sensor behavior over time.

\---

**## Important ML Rule**

The following identifiers are NOT used as ML model features:

\`\`\`text
asset_id

component_id

prediction_id

timestamp
\`\`\`

Identifiers are used only for:

\- Metadata

\- Component lookup

\- Final output

\- Integration

This prevents the ML models from memorizing specific assets or components.

\---

**# Random Forest**

**## Responsibility**

Random Forest predicts component failure risk.

**## Output**

\`\`\`text
failure_probability

risk_category
\`\`\`

**### Failure Probability**

Range:

\`\`\`text
0.0 to 1.0
\`\`\`

**### Risk Categories**

\`\`\`text
LOW

MEDIUM

HIGH
\`\`\`

The probability is generated using:

\`\`\`python
RandomForestClassifier.predict_proba()
\`\`\`

The probability is generated through real model inference.

It is NOT hardcoded.

\---

**# Isolation Forest**

**## Responsibility**

Isolation Forest detects unusual component sensor behavior.

**## Output**

\`\`\`text
anomaly_score

anomaly_status

anomaly_severity

sensor
\`\`\`

**### Anomaly Status**

Contract-defined values:

\`\`\`text
NORMAL

HIGH
\`\`\`

Raw Isolation Forest values are not exposed directly as the final user-facing anomaly classification.

\---

**# Sensor Identification**

Isolation Forest provides a component-level anomaly result.

AssetSentinel also determines which sensor shows the strongest abnormal behavior.

The system evaluates engineered behavior for:

\`\`\`text
vibration

temperature

pressure

RPM
\`\`\`

Indicators can include:

\- Maximum z-score

\- Trend slope

\- Latest value compared with rolling mean

The final sensor output is one of:

\`\`\`text
vibration

temperature

pressure

RPM

NONE
\`\`\`

\---

**# Anomaly Severity**

Anomaly severity values are:

\`\`\`text
LOW

MEDIUM

HIGH
\`\`\`

Severity is determined using centralized deterministic thresholds based on the magnitude of abnormal sensor behavior.

For example:

\`\`\`text
NORMAL

    ↓

LOW

    ↓

Moderate abnormal behavior

    ↓

MEDIUM

    ↓

Strong abnormal behavior

    ↓

HIGH
\`\`\`

\---

**# ML Prediction Service**

The Member 2 ML module provides a reusable prediction interface.

Public functionality supports:

\`\`\`text
Single component prediction
\`\`\`

and:

\`\`\`text
All component prediction
\`\`\`

The prediction service:

1\. Loads trained Random Forest artifacts

2\. Loads trained Isolation Forest artifacts

3\. Loads saved feature column definitions

4\. Reuses the existing feature engineering pipeline

5\. Runs real model inference

6\. Produces contract-compliant results

Models are cached where appropriate to avoid unnecessary repeated loading.

\---

**# Contract-Compliant ML Result**

The combined internal prediction result contains the information required by the shared contract.

Example:

\`\`\`json
{
  "prediction_id": "PRED-XXXXXXX",
  "asset_id": "AS-1047",
  "component_id": "BRG-1047",
  "failure_probability": 0.899,
  "risk_category": "HIGH",
  "anomaly_score": -0.056,
  "anomaly_status": "HIGH",
  "anomaly_severity": "HIGH",
  "sensor": "vibration",
  "timestamp": "2026-09-13T09:50:36+00:00"
}
\`\`\`

The backend can separate the Random Forest and Isolation Forest fields when storing or exposing them.

\---

**# Evidence Layer Architecture**

\`\`\`text
Member 2 ML Output

        │

        ▼

Failure Prediction

+

Anomaly Detection

        │

        ▼

Member 3 Evidence Layer

        │

        ├── Maintenance Status

        ├── Component Criticality

        └── Mission Information

        │

        ▼

Canonical Evidence Object
\`\`\`

The Evidence Layer combines ML evidence with operational context.

ML does not calculate the final readiness decision.

\---

**# Readiness Architecture**

\`\`\`text
Canonical Evidence Object

        │

        ▼

Hard Rules

        │

        ├── Critical inspection overdue

        ├── Critical component risk threshold exceeded

        └── Required component unavailable

        │

        ▼

Readiness Score

        │

        ├── READY

        ├── CONDITIONALLY READY

        └── NOT READY
\`\`\`

The Readiness Engine is responsible for the final readiness decision.

The LLM does not independently determine readiness.

\---

**# Maintenance Architecture**

\`\`\`text
Evidence Object

        │

        ├── Failure Risk

        ├── Criticality

        ├── Mission Impact

        └── Maintenance Context

        │

        ▼

Maintenance Priority Engine

        │

        ▼

Ranked Maintenance Actions
\`\`\`

The ML module provides evidence.

The Maintenance Engine determines priorities.

\---

**# End-to-End Data Flow**

\`\`\`text
Sensor Data

        │

        ▼

Data Loading

        │

        ▼

Validation

        │

        ▼

Feature Engineering

        │

        ├───────────────┐

        │               │

        ▼               ▼

Random Forest      Isolation Forest

        │               │

        └───────┬───────┘

                │

                ▼

        ML Prediction Service

                │

                ▼

           Member 1 Backend

                │

                ▼

           Member 3 Evidence

                │

                ▼

           Readiness Engine

                │

                ▼

          Maintenance Engine

                │

                ▼

            FastAPI APIs

                │

                ▼

           React Frontend
\`\`\`

\---

**# IBM watsonx.ai Web Copilot Architecture**

The AssetSentinel web copilot uses IBM watsonx.ai as the actual AI model runtime.

\`\`\`text
Human Operator

      ↓

React Copilot UI

      ↓

FastAPI Chat Endpoint

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

Grounded Explanation

      ↓

React Copilot UI
\`\`\`

The web copilot is not based on hardcoded responses or keyword-only intent matching.

The chatbot delegates AI processing to the real IBM watsonx.ai integration.

\---

**## Watsonx Service**

The Watsonx integration is implemented in:

\`\`\`text
app/services/watsonx_service.py
\`\`\`

The service:

\- Loads Watsonx configuration from environment variables

\- Initializes the IBM Watsonx chat model

\- Binds AssetSentinel tools

\- Sends user messages to IBM watsonx.ai

\- Processes tool calls

\- Retrieves live AssetSentinel data

\- Provides grounded context to the model

\- Returns the generated explanation to the frontend

The service uses:

\`\`\`text
WATSONX_API_KEY

WATSONX_PROJECT_ID

WATSONX_URL

WATSONX_MODEL_ID
\`\`\`

\---

**## Chat Service**

The web chat entry point is:

\`\`\`text
app/services/chat_service.py
\`\`\`

The chat service delegates message processing to:

\`\`\`text
process_message_with_watsonx()
\`\`\`

This keeps the chat API compatible with the existing backend while allowing IBM watsonx.ai to perform the actual language-model processing.

\---

**# Shared Copilot Tools**

AssetSentinel uses a shared tool layer:

\`\`\`text
app/services/copilot_tools.py
\`\`\`

The shared tools provide live database-backed information to AI integrations.

This prevents duplicate or hardcoded data-access logic.

The same underlying project information can therefore be accessed by:

\- IBM watsonx.ai web copilot

\- IBM Bob through MCP

The tools remain read-only.

\---

**# Grounded Copilot Behavior**

The copilot must use tools for factual project information.

The copilot must NOT invent:

\- Asset status

\- Component health

\- Failure probabilities

\- Risk categories

\- Anomalies

\- Sensor trends

\- Maintenance history

\- Mission readiness

\- Fleet readiness

\- Maintenance priorities

If requested information does not exist, the copilot must clearly state that the data is unavailable.

Example:

\`\`\`text
User:

What is the status of AS-FAKE-999?

        ↓

AssetSentinel Tool

        ↓

Asset Not Found

        ↓

IBM watsonx.ai

        ↓

Grounded Response
\`\`\`

Expected behavior:

\`\`\`text
The asset AS-FAKE-999 was not found in the system.
Please verify the asset ID and try again.
\`\`\`

The AI must not fabricate a status for an unknown asset.

\---

**# IBM Bob Integration**

**## IBM Bob Role**

IBM Bob is integrated with AssetSentinel through the Model Context Protocol.

IBM Bob is used as:

\- AI-assisted development environment

\- Project workflow environment

\- MCP host for AssetSentinel tools

\- Grounded interaction interface for AssetSentinel data

IBM Bob is not the authority for readiness decisions.

The Readiness Engine remains responsible for readiness evaluation.

\---

**# MCP Integration**

The AssetSentinel MCP Server provides read-only access to structured system information.

The MCP server is implemented in:

\`\`\`text
app/mcp_server.py
\`\`\`

The project-level IBM Bob MCP configuration is:

\`\`\`text
.bob/mcp.json
\`\`\`

The MCP integration provides 11 read-only tools.

\---

**## MCP Tools**

The available tools are:

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

These tools provide structured AssetSentinel information to IBM Bob.

\---

**## MCP Data Flow**

\`\`\`text
IBM Bob IDE

      ↓

.bob/mcp.json

      ↓

AssetSentinel MCP Server

      ↓

Shared Copilot Tools

      ↓

Live AssetSentinel Data

      ↓

Structured Results

      ↓

IBM Bob

      ↓

Grounded Explanation
\`\`\`

The MCP server does not independently make operational decisions.

\---

**## MCP Safety Boundary**

The MCP tools are read-only.

They do not:

\- Modify asset state

\- Modify database records

\- Change readiness decisions

\- Execute maintenance actions

\- Control physical assets

\- Modify ML predictions

\- Override backend rules

IBM Bob receives information from AssetSentinel and can explain that information, but it does not replace the deterministic system components.

\---

**# Important IBM Architecture Boundary**

AssetSentinel uses IBM watsonx.ai and IBM Bob for different but complementary purposes.

\`\`\`text
                    ASSETSENTINEL
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
    WEB COPILOT                    IBM BOB IDE
          │                             │
          ▼                             ▼
 IBM watsonx.ai                       MCP
          │                             │
          ▼                             ▼
 Shared Copilot Tools          AssetSentinel MCP Server
          │                             │
          └──────────────┬──────────────┘
                         │
                         ▼
                Live AssetSentinel Data
\`\`\`

The web application uses IBM watsonx.ai as its LLM runtime.

IBM Bob connects through MCP.

The architecture does NOT claim that IBM Bob itself is embedded as a web chatbot.

\---

**# Canonical Demo Flow — AS-1047**

**## 1. Sensor Behavior**

AS-1047 contains increasing vibration behavior associated with its bearing component.

\---

**## 2. Feature Engineering**

The system calculates historical sensor behavior indicators such as:

\- Rolling statistics

\- Trend slope

\- Maximum z-score

\- Latest value compared with historical behavior

\---

**## 3. Random Forest**

The trained Random Forest performs real inference.

Example result:

\`\`\`text
failure_probability ≈ 0.899

risk_category = HIGH
\`\`\`

\---

**## 4. Isolation Forest**

The trained Isolation Forest performs anomaly inference.

Example result:

\`\`\`text
anomaly_status = HIGH

anomaly_severity = HIGH

sensor = vibration
\`\`\`

The sensor is determined from engineered behavior indicators.

There is no rule such as:

\`\`\`python
if asset_id == "AS-1047":
\`\`\`

The result emerges from the data and model inference.

\---

**## 5. Backend**

The backend receives the prediction and anomaly results.

It exposes the information through prediction APIs.

\---

**## 6. Evidence Layer**

The Evidence Layer combines:

\`\`\`text
Failure Risk

+

Anomaly Information

+

Maintenance Context

+

Component Criticality

+

Mission Information
\`\`\`

This produces the canonical Evidence Object.

\---

**## 7. Readiness Engine**

The Readiness Engine evaluates:

\- Hard rules

\- Evidence

\- Readiness scoring

It produces one of:

\`\`\`text
READY

CONDITIONALLY READY

NOT READY
\`\`\`

\---

**## 8. Maintenance Engine**

The Maintenance Engine uses operational evidence to prioritize maintenance actions.

\---

**## 9. Frontend**

The React frontend displays:

\- Predictions

\- Anomalies

\- Readiness

\- Maintenance priorities

\- Asset information

\- Mission information

\- Copilot responses

\---

**## 10. Watsonx Copilot**

An operator can ask:

\`\`\`text
Why is AS-1047 not ready?
\`\`\`

The web copilot:

1\. Sends the question to the FastAPI backend.

2\. Sends the request to IBM watsonx.ai.

3\. Uses the appropriate AssetSentinel tool.

4\. Retrieves actual project evidence.

5\. Provides the evidence to the model.

6\. Generates a grounded explanation.

The LLM explains the backend result.

It does not independently decide readiness.

\---

**# Conversation Context**

The Watsonx service maintains bounded conversation context.

This allows follow-up questions such as:

\`\`\`text
User:

What is the status of AS-1047?

Assistant:

[Grounded AS-1047 response]

User:

Why?

Assistant:

[Grounded explanation using available context and tools]
\`\`\`

Conversation context is bounded to avoid unbounded memory growth.

\---

**# Frontend Copilot**

The main copilot interface is implemented in:

\`\`\`text
IBMBob.tsx
\`\`\`

The interface provides:

\- Welcome state

\- Conversation messages

\- User input

\- Suggested questions

\- Loading / typing indicator

\- Watsonx responses

\- Chat history

\- New chat functionality

\- Persistent conversation state

The frontend is responsible for presentation and user interaction.

It does not contain readiness or ML decision logic.

\---

**# Chat Persistence**

Conversation history is maintained separately from operational AssetSentinel data.

The frontend can persist conversations using browser local storage.

Logical storage keys include:

\`\`\`text
ibm_bob_chat_history

ibm_bob_active_chat_id
\`\`\`

This allows conversations to survive:

\- Component unmount

\- Page navigation

\- Browser refresh

Conversation persistence does not modify the AssetSentinel operational database.

\---

**# End-to-End Copilot Example**

\`\`\`text
Operator

   │

   ▼

"What anomalies were detected on AS-1047?"

   │

   ▼

React Copilot

   │

   ▼

FastAPI

   │

   ▼

IBM watsonx.ai

   │

   ▼

get_anomalies("AS-1047")

   │

   ▼

AssetSentinel Database

   │

   ▼

Anomaly Data

   │

   ▼

IBM watsonx.ai

   │

   ▼

Grounded Explanation

   │

   ▼

React Copilot

   │

   ▼

Operator
\`\`\`

\---

**# End-to-End IBM Bob Example**

\`\`\`text
IBM Bob

   │

   ▼

MCP

   │

   ▼

AssetSentinel MCP Server

   │

   ▼

get_asset_status("AS-1047")

   │

   ▼

Shared Copilot Tools

   │

   ▼

AssetSentinel Database

   │

   ▼

Structured Asset Data

   │

   ▼

IBM Bob

   │

   ▼

Grounded Explanation
\`\`\`

\---

**# Component Table**

\| Component | Location / Module | Responsibility |
\|---|---|---|
\| Data Loading | Member 2 ML | Load and validate sensor data |
\| Feature Engineering | Member 2 ML | Generate historical sensor behavior features |
\| Random Forest | Member 2 ML | Predict failure probability and risk category |
\| Isolation Forest | Member 2 ML | Detect anomalies and anomaly severity |
\| Prediction Service | Member 2 ML | Provide reusable contract-compliant ML predictions |
\| Backend | Member 1 | APIs, database integration, prediction persistence |
\| Chat Service | Member 1 | Route web copilot requests to Watsonx |
\| Watsonx Service | Member 1 | IBM watsonx.ai LLM and tool-calling integration |
\| Shared Copilot Tools | Integration Layer | Provide live database-backed copilot information |
\| Evidence Layer | Member 3 | Combine ML and operational evidence |
\| Readiness Engine | Member 3 | Evaluate readiness using evidence and rules |
\| Maintenance Engine | Member 3 | Rank maintenance actions |
\| FastAPI | Member 1 | Backend API layer |
\| SQLAlchemy Models | Member 1 | Database models |
\| Pydantic Schemas | Member 1 | API request and response validation |
\| MCP Server | Integration Layer | Provide read-only AssetSentinel tools |
\| IBM Bob | IBM Integration | MCP-based development and grounded system interaction |
\| React Frontend | Frontend | User interface and dashboard |
\| IBMBob.tsx | Frontend | Web copilot interface and conversation state |

\---

**# Technology Stack**

\| Layer | Technology |
\|---|---|
\| Frontend | React, TypeScript, Vite, Tailwind CSS, Recharts, Axios |
\| Backend | Python, FastAPI, Uvicorn, Pydantic |
\| Database | SQLite, SQLAlchemy |
\| Data Processing | Pandas, NumPy |
\| Machine Learning | scikit-learn |
\| Failure Prediction | Random Forest |
\| Anomaly Detection | Isolation Forest |
\| Web AI Copilot | IBM watsonx.ai |
\| AI Integration | LangChain IBM / ChatWatsonx |
\| IBM Developer Integration | IBM Bob |
\| Agent Integration | Model Context Protocol (MCP) |
\| API Integration | REST APIs |
\| Development | Git, GitHub |

\---

**# Project Structure**

\`\`\`text
AssetSentinel/

├── src/

│   ├── frontend/

│   │   └── ...

│   │
│   ├── backend/

│   │   └── member1_backend/

│   │       ├── app/

│   │       │   ├── services/

│   │       │   │   ├── chat_service.py

│   │       │   │   ├── watsonx_service.py

│   │       │   │   └── copilot_tools.py

│   │       │   │
│   │       │   └── mcp_server.py

│   │       │
│   │       └── ...

│   │
│   ├── .env

│   └── .env.example

│
├── .bob/

│   └── mcp.json

│
├── ...

└── ARCHITECTURE.md
\`\`\`

\---

**# Environment Configuration**

The Watsonx integration uses environment variables.

Example:

\`\`\`env
WATSONX_API_KEY=your_api_key_here

WATSONX_PROJECT_ID=your_project_id_here

WATSONX_URL=https://<region>.ml.cloud.ibm.com

WATSONX_MODEL_ID=your_supported_model_id

DATABASE_URL=sqlite:///./asset_sentinel.db

APP_PORT=8000

APP_ENV=development
\`\`\`

The actual `.env` file is local and must never be committed.

Only the template should be committed:

\`\`\`text
src/.env.example
\`\`\`

\---

**# IBM watsonx.ai Runtime Requirements**

The Watsonx integration requires:

\- IBM Cloud API credentials

\- Watsonx project ID

\- Associated Watsonx Runtime service

\- Correct regional Watsonx endpoint

\- A model supported by the selected Watsonx environment

The application performs real IBM authentication and model inference.

The following are NOT used as substitutes for Watsonx:

\`\`\`text
Hardcoded chatbot responses

Regex-only intent matching

Keyword-only response generation

Fake Watsonx responses

Static JSON pretending to be AI output
\`\`\`

\---

**# Validation Strategy**

The project should validate every major layer independently.

**## Backend**

Test:

\- API endpoints

\- Database access

\- Prediction retrieval

\- Anomaly retrieval

\- Evidence integration

\- Readiness results

\- Maintenance priorities

\- Chat endpoint

**## Machine Learning**

Test:

\- Data loading

\- Feature engineering

\- Random Forest inference

\- Isolation Forest inference

\- Contract compliance

\- Edge cases

**## Watsonx**

Test:

\- API key authentication

\- Project access

\- Runtime service association

\- Model availability

\- Chat API call

\- Tool calling

\- Grounded responses

\- Missing asset behavior

\- Follow-up questions

**## MCP**

Test:

\- MCP server startup

\- Tool discovery

\- Tool schemas

\- Read-only behavior

\- Live database results

\- IBM Bob connection

**## Frontend**

Test:

\- Dashboard rendering

\- API integration

\- Copilot interaction

\- Loading state

\- Chat history

\- New chat

\- Conversation persistence

\- Responsive layout

\---

**# Watsonx Verification**

A successful Watsonx integration should be validated through the actual backend request path.

Expected flow:

\`\`\`text
React

  ↓

FastAPI

  ↓

watsonx_service.py

  ↓

IBM Authentication

  ↓

IBM watsonx.ai Chat API

  ↓

Tool Calls

  ↓

Live AssetSentinel Data

  ↓

Watsonx Response

  ↓

React
\`\`\`

A successful backend request to the Watsonx chat endpoint confirms that the application reached the actual Watsonx service.

A frontend HTTP 200 response alone does not prove that the LLM was contacted.

\---

**# IBM Bob MCP Verification**

The IBM Bob integration should be verified using the actual IBM Bob environment.

Validation steps:

1\. Open the AssetSentinel project in IBM Bob.

2\. Ensure `.bob/mcp.json` is present.

3\. Start or enable the AssetSentinel MCP server.

4\. Confirm the MCP server is connected.

5\. Ask IBM Bob to discover the AssetSentinel tools.

6\. Invoke a read-only tool such as:

\`\`\`text
get_asset_status("AS-1047")
\`\`\`

7\. Confirm that the returned information matches live AssetSentinel data.

A local MCP test validates the MCP server itself.

Actual IBM Bob interaction validates the Bob-to-MCP integration.

\---

**# Trust and Decision Boundaries**

AssetSentinel intentionally separates AI explanation from operational decision-making.

\`\`\`text
ML

↓

Provides evidence

↓

Evidence Layer

↓

Combines evidence

↓

Readiness Engine

↓

Makes readiness decision

↓

Maintenance Engine

↓

Ranks maintenance actions

↓

IBM watsonx.ai / IBM Bob

↓

Explains retrieved information
\`\`\`

This prevents the conversational AI layer from overriding deterministic project logic.

\---

**# Security and Trust Notes**

\- All project data is synthetic.

\- No real operational or classified data is used.

\- AssetSentinel is a decision-support prototype.

\- The system does not autonomously control assets.

\- Human operators retain final authority.

\- ML predictions are treated as evidence, not autonomous decisions.

\- Readiness decisions are produced by the Readiness Engine.

\- IBM watsonx.ai does not override readiness decisions.

\- IBM Bob does not override readiness decisions.

\- MCP tools are read-only.

\- The frontend does not calculate readiness.

\- IBM credentials must remain local.

\- No API keys or secrets should be committed to the repository.

\- `.env` must be excluded through `.gitignore`.

\---

**# Final Architecture Summary**

AssetSentinel combines machine learning, deterministic decision logic, operational evidence, and IBM AI technologies into a mission-readiness and predictive-maintenance workflow.

The primary system flow is:

\`\`\`text
Sensor Data

    ↓

ML Detection

    ↓

Evidence

    ↓

Readiness

    ↓

Maintenance

    ↓

Backend APIs

    ↓

React Dashboard
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
IBM Bob IDE

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

The core architectural principle is:

**\*\*ML detects. Evidence combines. Readiness decides. Maintenance prioritizes. IBM AI explains.\*\***

**\*\*The AI layer explains AssetSentinel's computed results; it does not replace the system's readiness or maintenance decision engines.\*\***