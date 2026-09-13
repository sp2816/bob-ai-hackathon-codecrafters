"""
AssetSentinel — Synthetic Data Generator
Member 2 (Selin) | src/backend/member2_ml/data/generate_data.py

Purpose:
    Generates the four CSV datasets required by the Member 2 ML pipeline:
        assets.csv
        components.csv
        sensor_data.csv
        maintenance_records.csv

    All column names strictly follow the shared data contract:
        src/backend/integration/contracts/data-contracts.md

    Run once to regenerate all CSVs:
        python src/backend/member2_ml/data/generate_data.py

Architecture position:
    Raw data (this script)
        → preprocessing/data_loader.py          (Phase 2)
        → features/feature_engineering.py       (Phase 3)
        → models/training/train_model.py         (Phase 4)
        → prediction/predict.py                  (Phase 5)
        → prediction/anomaly_detection.py        (Phase 5)
        → evaluation/model_evaluation.py         (Phase 6)

IMPORTANT — this script only creates files inside:
    src/backend/member2_ml/
Do NOT modify shared contracts or any other member's folder.
"""

import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Reproducible seed — all randomness goes through numpy and random
# ---------------------------------------------------------------------------
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# ---------------------------------------------------------------------------
# Output directory — all CSVs land next to this script
# ---------------------------------------------------------------------------
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Dataset constants
# ---------------------------------------------------------------------------

# Total assets: 1 canonical high-risk (AS-1047) + 9 normal
NUM_ASSETS = 10

# Sensor readings per sensor type per asset
READINGS_PER_SENSOR = 200

# Time-series start and interval
TS_START = datetime(2024, 1, 1, 0, 0, 0)
TS_INTERVAL_MINUTES = 15  # one reading every 15 minutes

# Canonical demo asset IDs (data only — ML output is never hardcoded)
CANONICAL_ASSET_ID = "AS-1047"
CANONICAL_COMPONENT_ID = "BRG-1047"

# Sensor types — exactly as defined in contract §6
SENSOR_TYPES = ["vibration", "temperature", "pressure", "RPM"]

# Enum values — exactly as defined in contract §7 (maintenance status)
STATUS_COMPLETED = "COMPLETED"
STATUS_OVERDUE   = "OVERDUE"
STATUS_SCHEDULED = "SCHEDULED"

# Enum values — exactly as defined in contract §5 (criticality)
CRITICALITY_HIGH   = "HIGH"
CRITICALITY_MEDIUM = "MEDIUM"
CRITICALITY_LOW    = "LOW"

# ---------------------------------------------------------------------------
# Asset definitions
# ---------------------------------------------------------------------------
# Contract fields (§4): asset_id, asset_name, asset_type, unit,
#                        operational_hours, current_status
#
# current_status is a Readiness Engine output (Member 3).
# We store "UNKNOWN" here so Member 1's seeder can update it at runtime.
# readiness_score is also owned by Member 3 — not included in this file.

ASSET_DEFINITIONS = [
    # --- Canonical high-risk asset ---
    {
        "asset_id":          "AS-1047",
        "asset_name":        "Rotary Wing Asset 1047",
        "asset_type":        "aircraft",
        "unit":              "Unit-Alpha",
        "operational_hours": 2450.0,
        "current_status":    "UNKNOWN",
    },
    # --- 9 normal-condition assets ---
    {
        "asset_id":          "AS-1001",
        "asset_name":        "Fixed Wing Asset 1001",
        "asset_type":        "aircraft",
        "unit":              "Unit-Alpha",
        "operational_hours": 980.0,
        "current_status":    "UNKNOWN",
    },
    {
        "asset_id":          "AS-1002",
        "asset_name":        "Ground Vehicle 1002",
        "asset_type":        "ground_vehicle",
        "unit":              "Unit-Bravo",
        "operational_hours": 1200.0,
        "current_status":    "UNKNOWN",
    },
    {
        "asset_id":          "AS-1003",
        "asset_name":        "Rotary Wing Asset 1003",
        "asset_type":        "aircraft",
        "unit":              "Unit-Bravo",
        "operational_hours": 660.0,
        "current_status":    "UNKNOWN",
    },
    {
        "asset_id":          "AS-1004",
        "asset_name":        "Ground Vehicle 1004",
        "asset_type":        "ground_vehicle",
        "unit":              "Unit-Charlie",
        "operational_hours": 450.0,
        "current_status":    "UNKNOWN",
    },
    {
        "asset_id":          "AS-1005",
        "asset_name":        "Fixed Wing Asset 1005",
        "asset_type":        "aircraft",
        "unit":              "Unit-Charlie",
        "operational_hours": 1750.0,
        "current_status":    "UNKNOWN",
    },
    {
        "asset_id":          "AS-1006",
        "asset_name":        "Rotary Wing Asset 1006",
        "asset_type":        "aircraft",
        "unit":              "Unit-Delta",
        "operational_hours": 320.0,
        "current_status":    "UNKNOWN",
    },
    {
        "asset_id":          "AS-1007",
        "asset_name":        "Ground Vehicle 1007",
        "asset_type":        "ground_vehicle",
        "unit":              "Unit-Delta",
        "operational_hours": 890.0,
        "current_status":    "UNKNOWN",
    },
    {
        "asset_id":          "AS-1008",
        "asset_name":        "Fixed Wing Asset 1008",
        "asset_type":        "aircraft",
        "unit":              "Unit-Echo",
        "operational_hours": 1340.0,
        "current_status":    "UNKNOWN",
    },
    {
        "asset_id":          "AS-1009",
        "asset_name":        "Ground Vehicle 1009",
        "asset_type":        "ground_vehicle",
        "unit":              "Unit-Echo",
        "operational_hours": 570.0,
        "current_status":    "UNKNOWN",
    },
]

# ---------------------------------------------------------------------------
# Component definitions
# ---------------------------------------------------------------------------
# Contract fields (§5): component_id, asset_id, component_type, criticality,
#                        installation_date, operating_hours, life_limit
#
# Internal fields (for feature engineering only, not part of cross-module contract):
#   service_interval_hours  — inspection interval in operational hours
#   hours_at_last_service   — asset's operational_hours at the last completed service
#
# AS-1047 / BRG-1047 is configured so:
#   hours_since_service = operational_hours - hours_at_last_service
#                       = 2450.0 - 2030.0 = 420 h
#   service_interval_hours = 300 h
#   → overdue_flag = 1 (420 > 300) — drives the OVERDUE maintenance status

def build_component_definitions():
    """Return a list of component dicts for all 10 assets."""
    components = []
    install_base = datetime(2018, 1, 1).date()

    # ---- AS-1047 components ----
    # main_bearing — HIGH criticality, intentionally OVERDUE
    components.append({
        "component_id":         "BRG-1047",
        "asset_id":             "AS-1047",
        "component_type":       "main_bearing",
        "criticality":          CRITICALITY_HIGH,
        "installation_date":    str(datetime(2018, 3, 15).date()),
        "operating_hours":      2450.0,
        "life_limit":           5000.0,
        "service_interval_hours": 300.0,
        "hours_at_last_service":  2030.0,  # → hours_since_service = 420 (OVERDUE)
    })
    # engine — HIGH criticality, within service interval
    components.append({
        "component_id":         "ENG-1047",
        "asset_id":             "AS-1047",
        "component_type":       "engine",
        "criticality":          CRITICALITY_HIGH,
        "installation_date":    str(datetime(2018, 3, 15).date()),
        "operating_hours":      2450.0,
        "life_limit":           8000.0,
        "service_interval_hours": 500.0,
        "hours_at_last_service":  2200.0,  # → hours_since_service = 250 (current)
    })
    # hydraulics — MEDIUM criticality, current
    components.append({
        "component_id":         "HYD-1047",
        "asset_id":             "AS-1047",
        "component_type":       "hydraulics",
        "criticality":          CRITICALITY_MEDIUM,
        "installation_date":    str(datetime(2019, 6, 1).date()),
        "operating_hours":      2450.0,
        "life_limit":           6000.0,
        "service_interval_hours": 400.0,
        "hours_at_last_service":  2200.0,
    })

    # ---- Normal assets: 2 components each ----
    # Tuple: (asset_id, comp_id, comp_type, criticality,
    #         life_limit, svc_interval, hours_since_service)
    normal_configs = [
        ("AS-1001", "BRG-1001", "main_bearing",  CRITICALITY_HIGH,   5000, 300, 120),
        ("AS-1001", "ENG-1001", "engine",         CRITICALITY_HIGH,   8000, 500, 200),
        ("AS-1002", "ENG-1002", "engine",         CRITICALITY_HIGH,   8000, 500,  80),
        ("AS-1002", "HYD-1002", "hydraulics",     CRITICALITY_MEDIUM, 6000, 400, 150),
        ("AS-1003", "BRG-1003", "main_bearing",   CRITICALITY_HIGH,   5000, 300, 210),
        ("AS-1003", "AVN-1003", "avionics",       CRITICALITY_MEDIUM, 4000, 350, 100),
        ("AS-1004", "ENG-1004", "engine",         CRITICALITY_HIGH,   8000, 500,  60),
        ("AS-1004", "COM-1004", "communications", CRITICALITY_LOW,    3000, 600,  90),
        ("AS-1005", "BRG-1005", "main_bearing",   CRITICALITY_HIGH,   5000, 300, 180),
        ("AS-1005", "SEN-1005", "sensors",        CRITICALITY_MEDIUM, 4000, 350, 220),
        ("AS-1006", "ENG-1006", "engine",         CRITICALITY_HIGH,   8000, 500,  40),
        ("AS-1006", "HYD-1006", "hydraulics",     CRITICALITY_MEDIUM, 6000, 400,  70),
        ("AS-1007", "ENG-1007", "engine",         CRITICALITY_HIGH,   8000, 500, 130),
        ("AS-1007", "COM-1007", "communications", CRITICALITY_LOW,    3000, 600, 200),
        ("AS-1008", "BRG-1008", "main_bearing",   CRITICALITY_HIGH,   5000, 300,  90),
        ("AS-1008", "AVN-1008", "avionics",       CRITICALITY_MEDIUM, 4000, 350, 160),
        ("AS-1009", "ENG-1009", "engine",         CRITICALITY_HIGH,   8000, 500, 250),
        ("AS-1009", "SEN-1009", "sensors",        CRITICALITY_MEDIUM, 4000, 350,  30),
    ]

    op_hours_map = {a["asset_id"]: a["operational_hours"] for a in ASSET_DEFINITIONS}

    for (asset_id, comp_id, comp_type, crit,
         life_lim, svc_int, hrs_since) in normal_configs:
        op_h = op_hours_map[asset_id]
        components.append({
            "component_id":           comp_id,
            "asset_id":               asset_id,
            "component_type":         comp_type,
            "criticality":            crit,
            "installation_date":      str(install_base),
            "operating_hours":        op_h,
            "life_limit":             float(life_lim),
            "service_interval_hours": float(svc_int),
            "hours_at_last_service":  op_h - float(hrs_since),
        })

    return components


# ---------------------------------------------------------------------------
# Sensor baseline parameters
# ---------------------------------------------------------------------------
# Representative normal operating ranges for military rotary/fixed-wing assets.
SENSOR_BASELINES = {
    "vibration":   {"mean": 1.5,    "std": 0.15,  "unit": "mm/s"},
    "temperature": {"mean": 75.0,   "std": 2.0,   "unit": "degC"},
    "pressure":    {"mean": 180.0,  "std": 5.0,   "unit": "psi"},
    "RPM":         {"mean": 2200.0, "std": 50.0,  "unit": "rpm"},
}


def generate_normal_readings(asset_id, component_id, sensor_type,
                              n_readings, ts_start):
    """
    Generate n_readings of normal sensor data for one asset/component/sensor.

    Each asset gets a slightly different baseline (±10 % of mean) to ensure
    the Isolation Forest trains on per-asset-relative anomalies.
    """
    base = SENSOR_BASELINES[sensor_type]

    # Per-asset, per-sensor reproducible RNG
    asset_num  = int(asset_id.replace("AS-", ""))
    sensor_key = abs(hash(sensor_type)) % 10000
    rng = np.random.RandomState(asset_num * 100 + sensor_key)

    asset_offset = rng.uniform(-0.10, 0.10) * base["mean"]
    asset_mean   = base["mean"] + asset_offset
    asset_std    = base["std"]

    values = rng.normal(loc=asset_mean, scale=asset_std, size=n_readings)
    values = np.clip(values, base["mean"] * 0.4, base["mean"] * 2.5)

    rows = []
    for i, val in enumerate(values):
        ts = ts_start + timedelta(minutes=TS_INTERVAL_MINUTES * i)
        rows.append({
            "sensor_id":    f"SEN-{asset_id}-{sensor_type.upper()}-{i+1:04d}",
            "asset_id":     asset_id,
            "component_id": component_id,
            "timestamp":    ts.isoformat(),
            "sensor_type":  sensor_type,
            "value":        round(float(val), 4),
        })
    return rows


def generate_as1047_readings(n_readings, ts_start):
    """
    Generate the canonical AS-1047 degradation scenario sensor readings.

    Designed per assetsentinel-implementation-plan.md §H:

    vibration (component BRG-1047):
        rows   0–149  normal baseline ~1.5 mm/s (±1.5 σ)
        rows 150–199  linear ramp to ~4.8 mm/s
                      (≈ 3.5–4.0 σ above baseline by final row)
        This degradation signal is what Random Forest and Isolation Forest
        must detect. The actual failure_probability is NEVER hardcoded —
        it emerges from model inference on these features.

    temperature:
        rows   0–149  normal ~75 °C
        rows 150–199  mild correlated upward trend (+0.1 °C / reading)

    pressure:  normal throughout (~180 psi)  — fault isolated to bearing
    RPM:       normal throughout (~2200 rpm)
    """
    asset_id     = "AS-1047"
    component_id = "BRG-1047"
    rng = np.random.RandomState(1047)

    degradation_start = 150
    vib_normal_mean   = 1.5
    vib_normal_std    = 0.15
    final_vibration   = 4.8   # target at row 199

    # --- vibration ---
    vib = rng.normal(vib_normal_mean, vib_normal_std, n_readings)
    ramp_len   = n_readings - degradation_start
    ramp       = np.linspace(0.0, final_vibration - vib_normal_mean, ramp_len)
    ramp_noise = rng.normal(0.0, 0.08, ramp_len)
    vib[degradation_start:] = vib_normal_mean + ramp + ramp_noise
    vib = np.clip(vib, 0.1, 12.0)

    # --- temperature ---
    tmp = rng.normal(75.0, 2.0, n_readings)
    temp_ramp = np.zeros(n_readings)
    temp_ramp[degradation_start:] = np.linspace(0.0, 0.10 * ramp_len, ramp_len)
    tmp = np.clip(tmp + temp_ramp, 50.0, 150.0)

    # --- pressure (normal) ---
    prs = np.clip(rng.normal(180.0, 5.0, n_readings), 100.0, 280.0)

    # --- RPM (normal) ---
    rpm = np.clip(rng.normal(2200.0, 50.0, n_readings), 1200.0, 3500.0)

    readings = []
    sensor_arrays = {
        "vibration":   vib,
        "temperature": tmp,
        "pressure":    prs,
        "RPM":         rpm,
    }
    for sensor_type, values in sensor_arrays.items():
        for i, val in enumerate(values):
            ts = ts_start + timedelta(minutes=TS_INTERVAL_MINUTES * i)
            readings.append({
                "sensor_id":    f"SEN-{asset_id}-{sensor_type.upper()}-{i+1:04d}",
                "asset_id":     asset_id,
                "component_id": component_id,
                "timestamp":    ts.isoformat(),
                "sensor_type":  sensor_type,
                "value":        round(float(val), 4),
            })
    return readings


# ---------------------------------------------------------------------------
# Maintenance record generation
# ---------------------------------------------------------------------------

def generate_maintenance_records(components):
    """
    Generate maintenance_records.csv rows for all components.

    Contract fields (§7):
        maintenance_id, asset_id, component_id, maintenance_type,
        maintenance_date, technician_action, status, notes

    Allowed status values (§7): COMPLETED | OVERDUE | SCHEDULED

    Per-component logic:
        1. One COMPLETED record for the last inspection.
        2. One follow-up record:
              OVERDUE   if hours_since_service > service_interval_hours
              SCHEDULED otherwise

    AS-1047 / BRG-1047:
        hours_since_service = 420  >  service_interval = 300
        → follow-up record status = OVERDUE
        This OVERDUE status is the hard-rule trigger for Member 3's
        Readiness Engine (NOT_READY without even running the score).
    """
    records   = []
    counter   = 1
    techs     = ["T. Morgan", "J. Rivera", "S. Kim", "A. Patel", "D. Chen"]

    for comp in components:
        asset_id = comp["asset_id"]
        comp_id  = comp["component_id"]
        svc_int  = comp["service_interval_hours"]
        hours_since = comp["operating_hours"] - comp["hours_at_last_service"]

        # Approximate date of last service (rough conversion: 100 h ≈ 1 month)
        months_ago = max(1, int(comp["hours_at_last_service"] / 100))
        last_date  = (datetime.now() - timedelta(days=months_ago * 30)).date()
        tech       = random.choice(techs)

        # --- Last completed inspection ---
        records.append({
            "maintenance_id":    f"MNT-{counter:04d}",
            "asset_id":          asset_id,
            "component_id":      comp_id,
            "maintenance_type":  "INSPECTION",
            "maintenance_date":  str(last_date),
            "technician_action": (
                f"Routine inspection of {comp['component_type']}. "
                "Serviceable. No corrective action required."
            ),
            "status":            STATUS_COMPLETED,
            "notes": (
                f"Completed at {comp['hours_at_last_service']:.0f} "
                "operational hours."
            ),
        })
        counter += 1

        # --- Next inspection record ---
        if hours_since > svc_int:
            next_status  = STATUS_OVERDUE
            action_note  = (
                f"Inspection OVERDUE by {hours_since - svc_int:.0f} h. "
                f"{hours_since:.0f}h since last service "
                f"(interval: {svc_int:.0f}h). Immediate action required."
            )
        else:
            remaining    = svc_int - hours_since
            next_status  = STATUS_SCHEDULED
            action_note  = (
                f"Scheduled inspection in approximately {remaining:.0f} h. "
                "No immediate action required."
            )

        next_date = (datetime.now() + timedelta(days=14)).date()
        records.append({
            "maintenance_id":    f"MNT-{counter:04d}",
            "asset_id":          asset_id,
            "component_id":      comp_id,
            "maintenance_type":  "INSPECTION",
            "maintenance_date":  str(next_date),
            "technician_action": action_note,
            "status":            next_status,
            "notes": (
                f"Record created at {comp['operating_hours']:.0f} "
                "operational hours."
            ),
        })
        counter += 1

    return records


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------

def write_assets_csv(output_dir):
    """Write assets.csv — contract §4 fields."""
    rows = [
        {
            "asset_id":          a["asset_id"],
            "asset_name":        a["asset_name"],
            "asset_type":        a["asset_type"],
            "unit":              a["unit"],
            "operational_hours": a["operational_hours"],
            "current_status":    a["current_status"],
        }
        for a in ASSET_DEFINITIONS
    ]
    df   = pd.DataFrame(rows)
    path = os.path.join(output_dir, "assets.csv")
    df.to_csv(path, index=False)
    print(f"  +  assets.csv                — {len(df)} rows")
    return df


def write_components_csv(components, output_dir):
    """Write components.csv — contract §5 fields + internal service fields."""
    df   = pd.DataFrame(components)
    path = os.path.join(output_dir, "components.csv")
    df.to_csv(path, index=False)
    print(f"  +  components.csv            — {len(df)} rows")
    return df


def write_sensor_data_csv(components, output_dir):
    """Write sensor_data.csv — contract §6 fields."""
    all_readings = []

    # Canonical degraded asset — dedicated generator
    all_readings.extend(generate_as1047_readings(READINGS_PER_SENSOR, TS_START))

    # All other components — normal behaviour
    for comp in components:
        asset_id = comp["asset_id"]
        comp_id  = comp["component_id"]
        if asset_id == CANONICAL_ASSET_ID and comp_id == CANONICAL_COMPONENT_ID:
            continue  # already generated above
        for sensor_type in SENSOR_TYPES:
            all_readings.extend(
                generate_normal_readings(
                    asset_id, comp_id, sensor_type, READINGS_PER_SENSOR, TS_START
                )
            )

    df = pd.DataFrame(all_readings)
    df.sort_values(["asset_id", "sensor_type", "timestamp"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    path = os.path.join(output_dir, "sensor_data.csv")
    df.to_csv(path, index=False)
    print(f"  +  sensor_data.csv           — {len(df)} rows")
    return df


def write_maintenance_records_csv(components, output_dir):
    """Write maintenance_records.csv — contract §7 fields."""
    records = generate_maintenance_records(components)
    df      = pd.DataFrame(records)
    path    = os.path.join(output_dir, "maintenance_records.csv")
    df.to_csv(path, index=False)
    print(f"  +  maintenance_records.csv   — {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print()
    print("AssetSentinel — Synthetic Data Generator  (Member 2 / Selin)")
    print("=" * 65)
    print(f"  Reproducible seed       : {RANDOM_SEED}")
    print(f"  Output directory        : {OUTPUT_DIR}")
    print(f"  Assets                  : {NUM_ASSETS}")
    print(f"  Readings / sensor type  : {READINGS_PER_SENSOR}")
    print()

    components = build_component_definitions()

    write_assets_csv(OUTPUT_DIR)
    write_components_csv(components, OUTPUT_DIR)
    write_sensor_data_csv(components, OUTPUT_DIR)
    write_maintenance_records_csv(components, OUTPUT_DIR)

    print()
    print("Canonical demo scenario — AS-1047 / BRG-1047:")
    print("  component_type      : main_bearing (HIGH criticality)")
    print("  vibration rows 0-149: ~1.5 mm/s  (normal baseline)")
    print("  vibration rows 150+  : ramps to ~4.8 mm/s (strong anomaly)")
    print("  temperature rows 150+: mild correlated upward trend")
    print("  pressure / RPM       : normal throughout")
    print("  hours_since_service  : 420 h  (interval 300 h -> OVERDUE)")
    print()
    print("NOTE: AS-1047 failure_probability is NOT hardcoded here.")
    print("      It emerges from Random Forest inference on these features.")
    print()
    print("All CSVs written. Next step: Phase 2 — preprocessing/data_loader.py")


if __name__ == "__main__":
    main()
