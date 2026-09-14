# Problem Statement

## Background

Modern industrial and engineering operations depend heavily on the continuous health and reliability of physical assets and their critical components. Assets such as engines, bearings, pumps, and other mechanical systems generate large volumes of sensor data, including vibration, temperature, pressure, and RPM measurements.

Organizations must continuously determine whether an asset is operating normally, whether one or more components are showing signs of degradation, and whether the asset is safe and ready for operation.

Traditional maintenance approaches often rely on scheduled inspections, manually reviewed sensor readings, or reactive maintenance after a failure occurs. These approaches make it difficult to identify early warning signs of component degradation and to combine multiple sources of operational evidence into a clear decision.

As industrial systems become more complex, teams need an intelligent and integrated way to transform raw sensor data and maintenance information into actionable insights about component health, asset condition, and operational readiness.

---

## The Problem

Operations and maintenance teams face difficulty identifying component failures and abnormal behavior early enough to make informed decisions.

Raw sensor readings alone do not clearly indicate whether a component is healthy or degrading. Different sensors can exhibit different types of abnormal behavior, such as:

- Increasing vibration
- Rising temperature
- Abnormal pressure patterns
- Unusual RPM behavior
- Long-term sensor trends
- Sudden deviations from historical behavior

In addition, failure risk and sensor anomalies are different problems that require different forms of analysis.

A component may have:

- A high predicted probability of failure
- An unusual sensor behavior pattern
- Both a high failure risk and an anomaly
- Neither, indicating normal operation

Without an integrated system, teams must manually interpret sensor measurements, identify abnormal trends, estimate component risk, and combine this information with maintenance and operational context.

This creates a fragmented decision-making process and increases the risk that important warning signals are missed or identified too late.

The core problem is therefore:

> How can raw industrial sensor data and component information be transformed into reliable, explainable, and component-level predictions that help identify failure risk and abnormal behavior before a critical failure occurs?

AssetSentinel addresses this problem by providing a unified intelligent asset monitoring pipeline that:

1. Processes historical sensor data.
2. Engineers meaningful sensor behavior features.
3. Predicts component failure probability using Random Forest.
4. Detects abnormal sensor behavior using Isolation Forest.
5. Identifies the sensor contributing most strongly to an anomaly.
6. Classifies failure risk and anomaly severity.
7. Passes ML evidence into an Evidence Layer and Readiness Engine.
8. Supports maintenance and operational decision-making through a unified system.

---

## Who is Affected

The problem affects people and teams responsible for monitoring, maintaining, and operating industrial assets.

### Maintenance Engineers

Maintenance engineers need to identify components that are likely to fail and determine which components require attention.

Without predictive insights, they may rely primarily on:

- Scheduled maintenance
- Manual inspection
- Historical failures
- Individual sensor thresholds

This makes it difficult to prioritize components based on actual predicted risk.

---

### Operations Teams

Operations teams need to know whether equipment is operating normally and whether abnormal component behavior could affect continued operation.

They need clear answers to questions such as:

- Which component is at risk?
- How high is the failure probability?
- Is the component behaving abnormally?
- Which sensor is showing the strongest abnormal behavior?
- How severe is the anomaly?

---

### Asset Managers

Asset managers are responsible for monitoring the overall condition of assets and coordinating maintenance and operational decisions.

They need a consolidated view of:

- Component-level failure risk
- Sensor anomalies
- Component criticality
- Maintenance status
- Asset health
- Operational readiness

---

### Decision Makers

Managers and operational decision makers need reliable evidence before deciding whether an asset should continue operating or require intervention.

They should not need to manually interpret large volumes of raw sensor data to understand the condition of an asset.

---

## Why It Matters

Unexpected component failures can lead to:

- Equipment downtime
- Increased maintenance costs
- Operational delays
- Reduced asset availability
- Safety concerns
- Missed maintenance opportunities
- Poor maintenance prioritization

A component may gradually degrade over time before reaching a complete failure state. If this degradation is not detected early, maintenance teams may only become aware of the problem after the component has reached a critical condition.

At the same time, relying only on simple sensor thresholds can produce incomplete conclusions. A sensor value may still appear acceptable at a single point in time while its historical trend, variation, or deviation from normal behavior indicates a developing problem.

For example, increasing vibration behavior in a bearing can indicate mechanical degradation even when maintenance schedules alone do not identify an immediate issue.

This makes early detection important.

AssetSentinel improves decision-making by separating and analyzing two important signals:

### Failure Risk

Random Forest estimates:

- `failure_probability`
- `risk_category`

This helps identify components with an increased likelihood of failure.

### Sensor Anomaly

Isolation Forest evaluates engineered historical sensor behavior and provides:

- `anomaly_score`
- `anomaly_status`
- `anomaly_severity`
- `sensor`

This helps identify abnormal operational behavior and the sensor most strongly associated with the anomaly.

These results can then be used as evidence for higher-level decisions rather than forcing maintenance or readiness decisions directly inside the ML system.

---

## Why Existing Solutions Fall Short

Traditional approaches to asset monitoring often have important limitations.

### 1. Reactive Maintenance

Reactive maintenance addresses problems only after a failure has occurred.

This can result in:

- Unexpected downtime
- Higher repair costs
- Disrupted operations
- Reduced asset availability

It does not provide sufficient early warning about gradual component degradation.

---

### 2. Fixed Maintenance Schedules

Scheduled maintenance performs inspections or maintenance at predefined intervals.

While useful, scheduled maintenance does not always reflect the actual condition of a component.

A component may:

- Develop problems before its next scheduled inspection
- Remain healthy despite approaching a scheduled maintenance date

Scheduled maintenance alone cannot dynamically adapt to real sensor behavior.

---

### 3. Simple Sensor Thresholds

Basic monitoring systems often use fixed thresholds such as:

- Temperature > threshold
- Vibration > threshold
- Pressure outside allowed range

These rules can miss important historical patterns.

For example, a vibration value may not exceed a fixed threshold but may show:

- A strong increasing trend
- Unusually high variation
- A large deviation from historical behavior

Therefore, analyzing only individual sensor values can provide incomplete information.

---

### 4. Failure Prediction Without Anomaly Detection

A failure prediction model estimates the probability of failure but does not necessarily explain whether current sensor behavior is abnormal.

Failure risk and anomaly detection provide different perspectives.

AssetSentinel therefore uses:

- **Random Forest** for supervised failure-risk prediction.
- **Isolation Forest** for unsupervised anomaly detection.

This provides complementary information rather than relying on a single model.

---

### 5. Isolated ML Models Without Operational Context

A machine learning model alone cannot make a complete operational decision.

For example, a high-risk component may need to be evaluated together with:

- Maintenance status
- Component criticality
- Mission impact
- Other component evidence

Similarly, readiness should not be determined directly by an ML model.

AssetSentinel addresses this limitation through a layered architecture:

```text
Sensor Data
    ↓
Data Loading and Validation
    ↓
Feature Engineering
    ↓
Random Forest + Isolation Forest
    ↓
ML Prediction and Anomaly Evidence
    ↓
Evidence Layer
    ↓
Readiness and Maintenance Decision Engines
    ↓
Frontend