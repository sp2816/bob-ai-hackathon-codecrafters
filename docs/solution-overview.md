# Solution Overview

## What We Built

AssetSentinel is an intelligent asset monitoring and decision-support system designed to help teams understand the health and operational condition of industrial assets.

The system transforms sensor data into meaningful component-level insights. Instead of requiring users to manually analyze large volumes of vibration, temperature, pressure, and RPM readings, AssetSentinel automatically identifies:

- Components with a high probability of failure
- Components showing abnormal sensor behavior
- The sensor most strongly associated with an anomaly
- The severity of abnormal behavior
- Evidence related to component health
- Asset readiness and maintenance-related insights

AssetSentinel combines machine learning with an evidence-based decision architecture.

The system uses two complementary machine learning models:

- **Random Forest** predicts the probability that a component may fail and classifies its failure risk.
- **Isolation Forest** detects unusual sensor behavior and identifies the severity and most relevant sensor associated with the anomaly.

The ML results are then passed through the backend and Evidence Layer, where they can be combined with additional operational information such as maintenance status, component criticality, and mission impact.

This separation allows machine learning to focus on detecting risk and abnormal behavior while higher-level system components handle readiness and maintenance decisions.

---

## How It Works

AssetSentinel processes asset data through the following steps.

### 1. Sensor and Asset Data Is Collected

The system works with component and sensor information, including historical readings such as:

- Vibration
- Temperature
- Pressure
- RPM

The system also manages asset and component information required by the broader monitoring system.

---

### 2. Data Is Loaded and Validated

The data pipeline loads the available sensor and component data and performs validation before it is used by the machine learning models.

This helps ensure that:

- Required data is present
- Invalid or empty data is detected
- Feature inputs are valid
- Missing components and assets are handled clearly
- NaN and infinite values are not silently passed to the models

---

### 3. Historical Sensor Behavior Features Are Engineered

Raw sensor readings are transformed into meaningful historical behavior features.

For each sensor, the ML pipeline generates features such as:

- Latest value
- Rolling mean
- Rolling standard deviation
- Maximum value
- Trend slope
- Maximum z-score

These features allow the system to evaluate sensor behavior over time instead of relying only on a single sensor reading.

The ML models do not use:

- `asset_id`
- `component_id`

as prediction features.

Identifiers are only used to associate results with the correct asset and component.

---

### 4. Random Forest Predicts Failure Risk

The Random Forest model uses the engineered features to estimate the probability that a component may fail.

For every component, it produces:

- `failure_probability`
- `risk_category`

The failure probability is a value between `0.0` and `1.0`.

The result is classified into:

- `LOW`
- `MEDIUM`
- `HIGH`

This model provides a failure-risk perspective based on learned patterns from the training data.

---

### 5. Isolation Forest Detects Abnormal Behavior

The Isolation Forest evaluates engineered historical sensor behavior to identify unusual component behavior.

For every component, it produces:

- `anomaly_score`
- `anomaly_status`
- `anomaly_severity`
- `sensor`

The anomaly analysis determines whether the component's sensor behavior is consistent with the learned healthy baseline or represents abnormal behavior.

The system does not expose raw Isolation Forest values such as `-1` and `1` directly to downstream consumers. Instead, it provides contract-compliant semantic output.

---

### 6. The System Identifies the Most Abnormal Sensor

Isolation Forest provides a component-level anomaly result.

AssetSentinel also determines which sensor contributes the strongest abnormal behavior.

The system evaluates the engineered behavior of:

- Vibration
- Temperature
- Pressure
- RPM

It uses deterministic analysis of sensor behavior indicators such as:

- Maximum z-score
- Trend slope
- Latest value compared with rolling mean

The final sensor result identifies:

- `vibration`
- `temperature`
- `pressure`
- `RPM`

or:

- `NONE`

when no significant anomaly is detected.

---

### 7. ML Results Are Produced Through a Reusable Prediction Service

The prediction service loads the trained machine learning artifacts instead of retraining models during prediction.

The service provides reusable component-level prediction results containing fields defined by the shared data contract.

The ML output includes information such as:

- `prediction_id`
- `asset_id`
- `component_id`
- `failure_probability`
- `risk_category`
- `anomaly_score`
- `anomaly_status`
- `anomaly_severity`
- `sensor`
- `timestamp`

This allows other modules to consume consistent ML results.

---

### 8. The Backend Integrates Prediction and Anomaly Results

The backend receives and exposes the machine learning results.

Random Forest prediction results and Isolation Forest anomaly results are managed through the backend so they can be consumed by other parts of the application.

The backend provides prediction APIs including:

- `GET /predictions/`
- `GET /predictions/asset/{id}`
- `GET /predictions/anomalies`
- `GET /predictions/anomalies/asset/{id}`

This allows the frontend and downstream services to access prediction and anomaly information.

---

### 9. The Evidence Layer Combines ML Results with Operational Context

The Evidence Layer consumes the ML output and combines it with relevant operational information.

This can include:

- Failure probability
- Risk category
- Anomaly information
- Maintenance and inspection status
- Component criticality
- Mission impact

The Evidence Layer creates a structured evidence object that represents the available information about a component or asset.

The ML module itself does not calculate readiness or maintenance decisions.

---

### 10. Readiness and Maintenance Engines Use the Evidence

The Readiness and Maintenance layers consume the structured evidence rather than directly relying on raw ML model output.

This separation ensures that:

- ML models provide prediction evidence
- The Evidence Layer organizes and combines information
- The Readiness Engine makes readiness decisions
- Maintenance logic determines maintenance-related priorities

This creates a clear separation of responsibilities across the system.

---

### 11. Results Are Displayed to the User

The frontend provides users with access to prediction and anomaly information through the integrated application.

Users can view information about:

- Component failure risk
- Failure probability
- Sensor anomalies
- Anomaly severity
- The sensor associated with abnormal behavior
- Asset-level operational insights

This helps transform complex technical data into understandable information for users.

---

## Architecture Diagram

> See [`architecture.md`](architecture.md) for the detailed diagram.

The high-level AssetSentinel architecture is:

```text
                         ┌─────────────────────┐
                         │   Sensor / Asset    │
                         │       Data          │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Data Loading &    │
                         │     Validation      │
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
              ┌─────────────────────┴─────────────────────┐
              │                                           │
              ▼                                           ▼
   ┌─────────────────────────┐               ┌─────────────────────────┐
   │     Random Forest       │               │    Isolation Forest     │
   │                         │               │                         │
   │ Failure Probability     │               │ Anomaly Score           │
   │ Risk Category           │               │ Status                  │
   └────────────┬────────────┘               │ Severity                │
                │                            │ Sensor                  │
                │                            └────────────┬────────────┘
                │                                         │
                └────────────────────┬────────────────────┘
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
                         │ API + Data Storage  │
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
```

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Used Random Forest for failure prediction | Random Forest is a supervised machine learning model that can predict component failure probability using `predict_proba()` and classify components into LOW, MEDIUM, and HIGH risk categories. |
| Used Isolation Forest for anomaly detection | Isolation Forest is well suited for detecting unusual sensor behavior and identifying anomalies without requiring every possible abnormal pattern to be explicitly labeled. |
| Kept Random Forest and Isolation Forest as separate ML models | Failure prediction and anomaly detection solve different problems. Keeping them independent provides clearer, more reliable, and complementary insights. |
| Used historical sensor feature engineering | Features such as rolling mean, rolling standard deviation, trend slope, latest value, and maximum z-score capture sensor behavior over time instead of relying only on individual raw readings. |
| Excluded asset and component identifiers from ML features | `asset_id` and `component_id` are identifiers, not sensor behavior. Excluding them prevents the models from memorizing specific assets instead of learning real operational patterns. |
| Used a reusable ML Prediction Service | The prediction service provides a clean interface for the Backend and Evidence Layer to consume real ML inference without duplicating ML logic. |
| Loaded trained model artifacts instead of retraining | Saved Random Forest and Isolation Forest artifacts are loaded during prediction, avoiding unnecessary retraining and improving prediction efficiency. |
| Used deterministic sensor identification logic | Engineered sensor behavior indicators are used to identify the most abnormal sensor, making the result understandable without relying on SHAP or model feature importance. |
| Used a shared data contract as the single source of truth | `data-contracts.md` ensures that Member 1 Backend, Member 2 ML, and Member 3 Evidence/Readiness modules use consistent field names, types, and integration interfaces. |
| Separated ML from readiness and maintenance decisions | The ML module provides prediction and anomaly evidence only. Evidence, readiness, and maintenance decisions are handled by their respective modules to maintain clear architectural boundaries. |
| Used FastAPI and React for system integration | FastAPI exposes backend APIs for predictions and system data, while React provides an interactive interface for viewing asset health and prediction insights. |

## IBM Technologies Used

- **IBM Bob:** Used as an AI-assisted development environment during the development of AssetSentinel. IBM Bob supported the implementation workflow, including code development, module reviews, architecture verification, testing guidance, and maintaining clear boundaries between the Backend, Machine Learning, Evidence/Readiness, and Frontend modules.
