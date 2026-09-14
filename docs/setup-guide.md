# Setup Guide

> **This file is read by the automated evaluation pipeline. Be precise and complete.**

## Prerequisites

Before you begin, ensure you have the following installed:

- [ ] Python 3.11+
- [ ] Node.js 18+
- [ ] npm
- [ ] Git

## Environment Variables

No external API keys or cloud credentials are required for the core application.

The application uses:

- Synthetic sensor data
- Local machine learning models
- SQLite database
- Locally stored model artifacts

If the repository contains a `.env.example` file, copy it to `.env` if required by your local configuration:

```bash
cp .env.example .env
```

The core application does not require IBM watsonx.ai credentials, PostgreSQL credentials, or Slack webhook configuration.

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/sp2816/bob-ai-hackathon-codecrafters.git

# 2. Enter the project directory
cd bob-ai-hackathon-codecrafters

# 3. Install backend dependencies
pip install -r src/backend/member1_backend/requirements.txt
pip install -r src/backend/member2_ml/requirements.txt

# 4. Install frontend dependencies
cd src/frontend
npm install

# 5. Return to the project root
cd ../..
```

## Database Setup

The application uses SQLite with SQLAlchemy.

The database and required tables are initialized by the backend application and seed/integration setup. No separate PostgreSQL server or migration command is required for the core application.

Ensure that the backend dependencies are installed before starting the application.

## Running the Application

### Start the Backend

From the project root:

```bash
cd src/backend/member1_backend

uvicorn app.main:app --reload
```

The backend will typically run at:

```text
http://localhost:8000
```

You can access the FastAPI documentation at:

```text
http://localhost:8000/docs
```

### Start the Frontend

Open a separate terminal.

From the project root:

```bash
cd src/frontend

npm run dev
```

The frontend will typically be available at:

```text
http://localhost:5173
```

## Running Tests

From the project root, run the complete backend test suite:

```bash
pytest src/backend -v
```

To run only the Member 2 Machine Learning tests:

```bash
pytest src/backend/member2_ml/tests -v
```

The Member 2 ML tests verify:

- Synthetic data generation
- Data loading and validation
- Feature engineering
- Random Forest training and inference
- Isolation Forest anomaly detection
- Prediction service
- Contract-compliant prediction output
- Model artifact loading
- No model retraining during prediction

## Quick Demo

### 1. Start the Backend

```bash
cd src/backend/member1_backend

uvicorn app.main:app --reload
```

### 2. Start the Frontend

In a separate terminal:

```bash
cd src/frontend

npm run dev
```

### 3. Open the Application

Open the frontend URL shown by Vite, typically:

```text
http://localhost:5173
```

### 4. View Predictions

The backend exposes prediction APIs including:

```text
GET /predictions/
```

Get predictions for a specific asset:

```text
GET /predictions/asset/{id}
```

Get anomaly results:

```text
GET /predictions/anomalies
```

Get anomaly results for a specific asset:

```text
GET /predictions/anomalies/asset/{id}
```

Example:

```text
GET /predictions/asset/AS-1047
```

The prediction pipeline provides:

- Failure probability
- Risk category
- Anomaly score
- Anomaly status
- Anomaly severity
- Affected sensor
- Timestamp

The ML pipeline uses:

- Random Forest for failure probability and risk category
- Isolation Forest for anomaly detection and anomaly severity

## Architecture Overview

The main application flow is:

```text
Synthetic Sensor Data
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
React Frontend
```

The architectural principle is:

```text
ML detects → Evidence proves → Readiness Engine decides
→ Maintenance Engine prioritizes → IBM Bob explains
```

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError` | Install dependencies using `pip install -r src/backend/requirements.txt` |
| `pytest` command not found | Install pytest using `pip install pytest` |
| Frontend dependencies missing | Run `npm install` inside `src/frontend` |
| Backend does not start | Verify backend dependencies are installed and run the command from `src/backend/member1_backend` |
| Port 8000 already in use | Stop the existing process using port 8000 or run Uvicorn on another port |
| Port 5173 already in use | Stop the existing process or allow Vite to select another available port |
| ML artifact not found | Verify that trained model artifact files exist in the expected Member 2 ML artifact directory |
| ML prediction fails | Run `pytest src/backend/member2_ml/tests -v` to verify the ML pipeline |
| Database errors | Verify the SQLite database path and SQLAlchemy configuration |
| API endpoint not responding | Confirm the FastAPI backend is running on the expected port |
| Frontend cannot connect to backend | Verify the backend URL and CORS configuration |
| Prediction API returns no data | Verify that database initialization, seed data, and ML/backend integration have completed |
| Git merge conflicts | Resolve conflicts manually, then run `git add .` followed by `git commit` |
| Import error for Member 2 ML | Verify Python paths and ensure `member2_ml` is available to the backend environment |
| Random Forest prediction fails | Verify the saved Random Forest model artifacts and feature columns are available |
| Isolation Forest prediction fails | Verify the saved Isolation Forest model artifacts and feature columns are available |