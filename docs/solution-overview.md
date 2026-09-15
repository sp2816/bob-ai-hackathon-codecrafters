**# Solution Overview**

**## What We Built**

AssetSentinel is an intelligent asset monitoring and decision-support system designed to help teams understand the health, operational condition, readiness, and maintenance status of industrial assets.

The system transforms sensor data into meaningful component-level insights. Instead of requiring users to manually analyze large volumes of vibration, temperature, pressure, and RPM readings, AssetSentinel automatically identifies:

\- Components with a high probability of failure

\- Components showing abnormal sensor behavior

\- The sensor most strongly associated with an anomaly

\- The severity of abnormal behavior

\- Evidence related to component health

\- Asset readiness and mission-related insights

\- Maintenance priorities

\- Fleet-level readiness information

AssetSentinel combines machine learning, evidence-based decision logic, and IBM AI technologies.

The system uses two complementary machine learning models:

\- **\*\*Random Forest\*\*** predicts the probability that a component may fail and classifies its failure risk.

\- **\*\*Isolation Forest\*\*** detects unusual sensor behavior and identifies anomaly status, severity, and the most relevant sensor.

The ML results are passed through the backend and Evidence Layer, where they can be combined with operational information such as maintenance status, component criticality, and mission impact.

AssetSentinel also provides an AI-powered web copilot using **IBM watsonx.ai**. The copilot uses shared database-backed tools to retrieve actual AssetSentinel information before generating an explanation.

The project also provides a real **IBM Bob MCP integration**, allowing IBM Bob to access AssetSentinel information through the Model Context Protocol using read-only tools.

This separation allows machine learning to focus on detecting risk and abnormal behavior while the Evidence Layer, Readiness Engine, and Maintenance Engine handle higher-level operational decisions.

\---

**## How It Works**

AssetSentinel processes asset data through the following steps.

**### 1. Sensor and Asset Data Is Collected**

The system works with component and sensor information, including historical readings such as:

\- Vibration

\- Temperature

\- Pressure

\- RPM

The system also manages asset, component, mission, and maintenance information required by the broader monitoring system.

The project uses synthetic sensor data for development, testing, and demonstration.

\---

**### 2. Data Is Loaded and Validated**

The data pipeline loads the available sensor and component data and performs validation before it is used by the machine learning models.

This helps ensure that:

\- Required data is present

\- Invalid or empty data is detected

\- Feature inputs are valid

\- Missing components and assets are handled clearly

\- NaN and infinite values are not silently passed to the models

\---

**### 3. Historical Sensor Behavior Features Are Engineered**

Raw sensor readings are transformed into meaningful historical behavior features.

For each sensor, the ML pipeline generates features such as:

\- Latest value

\- Rolling mean

\- Rolling standard deviation

\- Maximum value

\- Trend slope

\- Maximum z-score

These features allow the system to evaluate sensor behavior over time instead of relying only on a single sensor reading.

The ML models do not use:

\- \`asset\_id\`

\- \`component\_id\`

\- \`prediction\_id\`

\- \`timestamp\`

as prediction features.

Identifiers are used to associate results with the correct asset and component and for integration and metadata.

\---

**### 4. Random Forest Predicts Failure Risk**

The Random Forest model uses the engineered features to estimate the probability that a component may fail.

For every component, it produces:

\- \`failure\_probability\`

\- \`risk\_category\`

The failure probability is a value between \`0.0\` and \`1.0\`.

The result is classified into:

\- \`LOW\`

\- \`MEDIUM\`

\- \`HIGH\`

The model performs real inference using:

\`\`\`python
RandomForestClassifier.predict_proba()
\`\`\`

This model provides a failure-risk perspective based on learned patterns from the training data.

\---

**### 5. Isolation Forest Detects Abnormal Behavior**

The Isolation Forest evaluates engineered historical sensor behavior to identify unusual component behavior.

For every component, it produces:

\- \`anomaly\_score\`

\- \`anomaly\_status\`

\- \`anomaly\_severity\`

\- \`sensor\`

The anomaly analysis determines whether the component's sensor behavior is consistent with the learned healthy baseline or represents abnormal behavior.

The system does not expose raw Isolation Forest values such as \`-1\` and \`1\` directly to downstream consumers. Instead, it provides contract-compliant semantic output.

\---

**### 6. The System Identifies the Most Abnormal Sensor**

Isolation Forest provides a component-level anomaly result.

AssetSentinel also determines which sensor contributes the strongest abnormal behavior.

The system evaluates the engineered behavior of:

\- Vibration

\- Temperature

\- Pressure

\- RPM

It uses deterministic analysis of sensor behavior indicators such as:

\- Maximum z-score

\- Trend slope

\- Latest value compared with rolling mean

The final sensor result identifies:

\- \`vibration\`

\- \`temperature\`

\- \`pressure\`

\- \`RPM\`

or:

\- \`NONE\`

when no significant anomaly is detected.

\---

**### 7. ML Results Are Produced Through a Reusable Prediction Service**

The prediction service loads the trained machine learning artifacts instead of retraining models during prediction.

The service provides reusable component-level prediction results containing fields defined by the shared data contract.

The ML output includes information such as:

\- \`prediction\_id\`

\- \`asset\_id\`

\- \`component\_id\`

\- \`failure\_probability\`

\- \`risk\_category\`

\- \`anomaly\_score\`

\- \`anomaly\_status\`

\- \`anomaly\_severity\`

\- \`sensor\`

\- \`timestamp\`

This allows other modules to consume consistent ML results.

\---

**### 8. The Backend Integrates Prediction and Anomaly Results**

The backend receives and exposes the machine learning results.

Random Forest prediction results and Isolation Forest anomaly results are managed through the backend so they can be consumed by other parts of the application.

The backend provides prediction APIs including:

\- \`GET /predictions/\`

\- \`GET /predictions/asset/{id}\`

\- \`GET /predictions/anomalies\`

\- \`GET /predictions/anomalies/asset/{id}\`

This allows the frontend and downstream services to access prediction and anomaly information.

\---

**### 9. The Evidence Layer Combines ML Results with Operational Context**

The Evidence Layer consumes the ML output and combines it with relevant operational information.

This can include:

\- Failure probability

\- Risk category

\- Anomaly information

\- Maintenance and inspection status

\- Component criticality

\- Mission information

\- Mission impact

The Evidence Layer creates a structured evidence object that represents the available information about a component or asset.

The ML module itself does not calculate readiness or maintenance decisions.

\---

**### 10. Readiness and Maintenance Engines Use the Evidence**

The Readiness and Maintenance layers consume the structured evidence rather than directly relying on raw ML model output.

This separation ensures that:

\- ML models provide prediction evidence

\- The Evidence Layer organizes and combines information

\- The Readiness Engine makes readiness decisions

\- The Maintenance Engine determines maintenance-related priorities

This creates a clear separation of responsibilities across the system.

The Readiness Engine produces:

\- \`READY\`

\- \`CONDITIONALLY READY\`

\- \`NOT READY\`

The AI copilot does not override these decisions.

\---

**### 11. Results Are Displayed to the User**

The React frontend provides users with access to prediction, anomaly, readiness, maintenance, mission, and asset information.

Users can view information about:

\- Component failure risk

\- Failure probability

\- Sensor anomalies

\- Anomaly severity

\- The sensor associated with abnormal behavior

\- Asset-level operational insights

\- Readiness results

\- Maintenance priorities

\- Mission information

The copilot interface allows users to ask natural-language questions about the available AssetSentinel data.

\---

**### 12. IBM watsonx.ai Provides the Web Copilot**

AssetSentinel includes a real IBM watsonx.ai-powered web copilot.

The web copilot is integrated through the backend using:

\`\`\`text
app/services/chat_service.py

app/services/watsonx_service.py

app/services/copilot_tools.py
\`\`\`

The flow is:

\`\`\`text
User

    ↓

React Copilot

    ↓

FastAPI Chat API

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

React Copilot
\`\`\`

The copilot uses tools for factual project information.

It does not rely on hardcoded responses or regex-only intent matching.

The copilot must not invent:

\- Asset status

\- Failure probabilities

\- Risk categories

\- Anomalies

\- Sensor trends

\- Maintenance history

\- Readiness results

\- Mission information

If requested information is unavailable, the copilot reports that the data could not be found.

\---

**### 13. Shared Copilot Tools Provide Grounded Data**

AssetSentinel uses a shared tool layer implemented in:

\`\`\`text
app/services/copilot_tools.py
\`\`\`

The shared tools provide live database-backed information to the AI integration layers.

This allows IBM watsonx.ai and IBM Bob to access consistent AssetSentinel information.

The shared tool layer prevents duplicate data-access logic and reduces the possibility of hardcoded chatbot information.

The tools are read-only.

\---

**### 14. IBM Bob Connects Through MCP**

AssetSentinel provides a real IBM Bob MCP integration.

The MCP server is implemented in:

\`\`\`text
app/mcp_server.py
\`\`\`

The IBM Bob project configuration is:

\`\`\`text
.bob/mcp.json
\`\`\`

The MCP server exposes 11 read-only AssetSentinel tools:

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

The IBM Bob MCP flow is:

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

Structured Results

    ↓

IBM Bob Explanation
\`\`\`

The MCP tools are read-only and do not modify operational data.

\---

**### 15. AI Explanation Does Not Replace System Decisions**

The AI layer is intentionally separated from the deterministic decision engines.

The architecture follows:

\`\`\`text
ML detects

    ↓

Evidence combines

    ↓

Readiness Engine decides

    ↓

Maintenance Engine prioritizes

    ↓

IBM AI explains
\`\`\`

IBM watsonx.ai and IBM Bob explain information retrieved from AssetSentinel.

They do not replace or override:

\- ML inference

\- Evidence processing

\- Readiness decisions

\- Maintenance prioritization

This ensures that the AI layer remains a grounded explanation and interaction layer rather than the operational authority.

\---

**## Architecture Diagram**

\> See [\`architecture.md\`](architecture.md) for the detailed architecture diagram.

The high-level AssetSentinel architecture is:

\`\`\`text

                    ┌─────────────────────┐
                    │ Human Operator      │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
     ┌─────────────────────┐       ┌─────────────────────┐
     │ React Frontend      │       │ IBM Bob IDE         │
     │ Dashboard + Copilot │       │ MCP Integration     │
     └──────────┬──────────┘       └──────────┬──────────┘
                │                             │
                ▼                             ▼
     ┌─────────────────────┐       ┌─────────────────────┐
     │ FastAPI Backend     │       │ AssetSentinel MCP   │
     │                     │       │ Server              │
     └──────────┬──────────┘       └──────────┬──────────┘
                │                             │
                │                             │
                └──────────────┬──────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Shared Copilot      │
                    │ Tools               │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ SQLite + SQLAlchemy │
                    │ AssetSentinel Data  │
                    └─────────────────────┘

Sensor Data
      │
      ▼
┌─────────────────────┐
│ Data Loading &      │
│ Validation          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Feature Engineering │
│                     │
│ • Rolling Mean      │
│ • Rolling Std       │
│ • Trend Slope       │
│ • Max Z-Score       │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│                                          │
▼                                          ▼
┌─────────────────────┐       ┌─────────────────────┐
│ Random Forest       │       │ Isolation Forest    │
│                     │       │                     │
│ Failure Probability │       │ Anomaly Score       │
│ Risk Category       │       │ Status              │
│                     │       │ Severity             │
│                     │       │ Sensor               │
└──────────┬──────────┘       └──────────┬──────────┘
           │                             │
           └──────────────┬──────────────┘
                          │
                          ▼
               ┌─────────────────────┐
               │ Member 2 ML         │
               │ Prediction Service  │
               └──────────┬──────────┘
                          │
                          ▼
               ┌─────────────────────┐
               │ Member 1 Backend    │
               │ API + Data Storage   │
               └──────────┬──────────┘
                          │
                          ▼
               ┌─────────────────────┐
               │ Member 3 Evidence   │
               │ Layer               │
               └──────────┬──────────┘
                          │
                          ▼
               ┌─────────────────────┐
               │ Readiness &         │
               │ Maintenance Engines │
               └──────────┬──────────┘
                          │
                          ▼
               ┌─────────────────────┐
               │ React Frontend      │
               │ Dashboard           │
               └─────────────────────┘
\`\`\`

The web copilot path is:

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

IBM watsonx.ai

    ↓

Grounded Explanation

    ↓

React Copilot
\`\`\`

The IBM Bob path is:

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

\---

**## Key Design Decisions**

\| Decision | Rationale |
\|---|---|
\| Used Random Forest for failure prediction | Random Forest is a supervised machine learning model that can predict component failure probability using \`predict\_proba()\` and classify components into LOW, MEDIUM, and HIGH risk categories. |
\| Used Isolation Forest for anomaly detection | Isolation Forest is well suited for detecting unusual sensor behavior and identifying anomalies without requiring every possible abnormal pattern to be explicitly labeled. |
\| Kept Random Forest and Isolation Forest as separate ML models | Failure prediction and anomaly detection solve different problems. Keeping them independent provides clearer, complementary insights. |
\| Used historical sensor feature engineering | Features such as rolling mean, rolling standard deviation, trend slope, latest value, and maximum z-score capture sensor behavior over time instead of relying only on individual raw readings. |
\| Excluded asset and component identifiers from ML features | \`asset\_id\`, \`component\_id\`, \`prediction\_id\`, and \`timestamp\` are identifiers or metadata rather than sensor behavior. Excluding them helps prevent the models from memorizing specific assets. |
\| Used a reusable ML Prediction Service | The prediction service provides a clean interface for the Backend and Evidence Layer to consume real ML inference without duplicating ML logic. |
\| Loaded trained model artifacts instead of retraining | Saved Random Forest and Isolation Forest artifacts are loaded during prediction, avoiding unnecessary retraining and improving prediction efficiency. |
\| Used deterministic sensor identification logic | Engineered sensor behavior indicators are used to identify the most abnormal sensor, making the result understandable without requiring SHAP or model feature importance. |
\| Used a shared data contract as the single source of truth | The shared data contracts ensure that Member 1 Backend, Member 2 ML, and Member 3 Evidence/Readiness modules use consistent field names, types, and integration interfaces. |
\| Separated ML from readiness and maintenance decisions | The ML module provides prediction and anomaly evidence only. Evidence, readiness, and maintenance decisions are handled by their respective modules to maintain clear architectural boundaries. |
\| Used FastAPI and React for system integration | FastAPI exposes backend APIs for predictions and system data, while React provides an interactive interface for viewing asset health, readiness, maintenance, and prediction insights. |
\| Used IBM watsonx.ai for the web copilot | IBM watsonx.ai provides the actual LLM runtime for the AssetSentinel web copilot, allowing natural-language interaction grounded in live project data. |
\| Used shared copilot tools | Shared database-backed tools allow the AI layer to retrieve actual AssetSentinel information rather than relying on hardcoded chatbot responses. |
\| Used tool-grounded AI responses | Factual project questions are answered using retrieved AssetSentinel data so that the copilot does not invent asset status, predictions, anomalies, maintenance history, or readiness information. |
\| Used IBM Bob with MCP | IBM Bob connects to the AssetSentinel MCP server through the Model Context Protocol, providing grounded access to read-only AssetSentinel tools. |
\| Kept MCP tools read-only | The MCP integration is designed for information retrieval and explanation and does not modify asset state, readiness decisions, maintenance records, or physical systems. |
\| Separated IBM watsonx.ai from IBM Bob | IBM watsonx.ai powers the AssetSentinel web copilot, while IBM Bob uses the MCP integration for IDE-based interaction. This accurately reflects the implemented architecture. |
| Kept AI separate from readiness authority | The Readiness Engine remains responsible for readiness decisions. IBM watsonx.ai and IBM Bob explain system results but do not override deterministic readiness logic. |
| Used synthetic project data | Synthetic data allows the system to demonstrate predictive maintenance and readiness workflows without exposing real operational or classified information. |

**## IBM Technologies Used**

\- **\*\*IBM watsonx.ai:\*\*** Used as the actual AI model runtime for the AssetSentinel web copilot. The Watsonx integration processes natural-language questions, invokes shared AssetSentinel tools, retrieves live project information, and generates grounded explanations.

\- **\*\*IBM Bob:\*\*** Used as an AI-assisted development and project workflow environment and integrated with AssetSentinel through MCP. IBM Bob can interact with the AssetSentinel MCP server and access structured, read-only project information.

\- **\*\*Model Context Protocol (MCP):\*\*** Used to connect IBM Bob with the AssetSentinel MCP server. The MCP server exposes 11 read-only tools for asset status, asset details, sensor trends, component health, failure predictions, anomalies, maintenance history, mission readiness, fleet readiness, maintenance priorities, and mission details.

\- **\*\*Shared Copilot Tools:\*\*** Provides a common database-backed tool layer used by the Watsonx web copilot and IBM Bob MCP integration, ensuring both AI interaction paths are grounded in the same AssetSentinel data.

\- **\*\*IBM AI Architecture Boundary:\*\*** IBM watsonx.ai powers the web copilot, while IBM Bob connects through MCP. Neither replaces the ML, Evidence, Readiness, or Maintenance engines.

**## Final Solution Summary**

AssetSentinel provides an end-to-end predictive maintenance and mission-readiness workflow:

\`\`\`text
Sensor Data

    ↓

Feature Engineering

    ↓

Random Forest + Isolation Forest

    ↓

Predictions + Anomalies

    ↓

Evidence Layer

    ↓

Readiness Engine

    ↓

Maintenance Engine

    ↓

FastAPI Backend

    ↓

React Frontend
\`\`\`

The AI interaction layer provides:

\`\`\`text
Web User

    ↓

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

Grounded Explanation
\`\`\`

The IBM Bob integration provides:

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

The core principle is:

\`\`\`text
ML detects → Evidence proves → Readiness Engine decides

→ Maintenance Engine prioritizes → IBM AI explains
\`\`\`

**\*\*The AI layer explains AssetSentinel results; it does not replace the system's readiness or maintenance decision engines.\*\***