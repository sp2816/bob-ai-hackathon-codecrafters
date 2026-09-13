"""
AssetSentinel — Data Loader Tests
Member 2 (Selin) | src/backend/member2_ml/tests/test_data_loader.py

Tests for preprocessing/data_loader.py (Phase 2).

Run with:
    pytest src/backend/member2_ml/tests/test_data_loader.py -v

All tests use the real CSVs from data/ so they validate the actual
generated data, not isolated mocks. This catches regressions if
generate_data.py is re-run with different parameters.

Tests are grouped by dataset, then by specific concern:
    - TestLoadAssets
    - TestLoadComponents
    - TestLoadSensorData
    - TestLoadMaintenanceRecords
    - TestReferentialIntegrity
    - TestLoadAndPrepareData
    - TestAS1047CanonicalScenario
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Make sure the member2_ml package root is on sys.path so relative imports
# work whether pytest is run from the repo root or from member2_ml/.
# ---------------------------------------------------------------------------
_ML_ROOT = Path(__file__).resolve().parent.parent   # …/member2_ml/
if str(_ML_ROOT) not in sys.path:
    sys.path.insert(0, str(_ML_ROOT))

from preprocessing.data_loader import (
    ALLOWED_MAINT_STATUS,
    ALLOWED_SENSOR_TYPES,
    PreparedDatasets,
    load_and_prepare_data,
    load_assets,
    load_components,
    load_maintenance_records,
    load_sensor_data,
    validate_referential_integrity,
)

# ---------------------------------------------------------------------------
# Shared fixture: load all datasets once per test session for speed
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def prepared() -> PreparedDatasets:
    """Load and validate all datasets once for the whole test session."""
    return load_and_prepare_data()


# ===========================================================================
# Assets
# ===========================================================================
class TestLoadAssets:
    def test_returns_dataframe(self, prepared):
        assert isinstance(prepared.assets, pd.DataFrame)

    def test_row_count(self, prepared):
        """Exactly 10 assets were generated."""
        assert len(prepared.assets) == 10

    def test_required_columns_present(self, prepared):
        required = [
            "asset_id", "asset_name", "asset_type", "unit",
            "operational_hours", "current_status",
        ]
        for col in required:
            assert col in prepared.assets.columns, f"Missing column: {col}"

    def test_no_duplicate_asset_ids(self, prepared):
        assert prepared.assets["asset_id"].is_unique

    def test_operational_hours_non_negative(self, prepared):
        assert (prepared.assets["operational_hours"] >= 0).all()

    def test_canonical_asset_present(self, prepared):
        """AS-1047 must be in the dataset."""
        assert "AS-1047" in prepared.assets["asset_id"].values

    def test_no_null_asset_ids(self, prepared):
        assert prepared.assets["asset_id"].notna().all()


# ===========================================================================
# Components
# ===========================================================================
class TestLoadComponents:
    def test_returns_dataframe(self, prepared):
        assert isinstance(prepared.components, pd.DataFrame)

    def test_required_columns_present(self, prepared):
        required = [
            "component_id", "asset_id", "component_type", "criticality",
            "installation_date", "operating_hours", "life_limit",
            "service_interval_hours", "hours_at_last_service",
        ]
        for col in required:
            assert col in prepared.components.columns, f"Missing column: {col}"

    def test_no_duplicate_component_ids(self, prepared):
        assert prepared.components["component_id"].is_unique

    def test_criticality_values_valid(self, prepared):
        invalid = ~prepared.components["criticality"].isin(
            ["LOW", "MEDIUM", "HIGH"]
        )
        assert not invalid.any(), (
            f"Invalid criticality values: "
            f"{prepared.components.loc[invalid, 'criticality'].unique()}"
        )

    def test_service_interval_positive(self, prepared):
        """service_interval_hours must be > 0 (used as denominator)."""
        assert (prepared.components["service_interval_hours"] > 0).all()

    def test_canonical_component_present(self, prepared):
        """BRG-1047 (main_bearing, HIGH, AS-1047) must be present."""
        brg = prepared.components[
            prepared.components["component_id"] == "BRG-1047"
        ]
        assert len(brg) == 1
        row = brg.iloc[0]
        assert row["asset_id"] == "AS-1047"
        assert row["component_type"] == "main_bearing"
        assert row["criticality"] == "HIGH"

    def test_as1047_bearing_overdue_setup(self, prepared):
        """
        hours_since_service for BRG-1047 must exceed service_interval_hours.
        This drives overdue_flag=1 in feature engineering.
        """
        brg = prepared.components[
            prepared.components["component_id"] == "BRG-1047"
        ].iloc[0]
        hours_since = brg["operating_hours"] - brg["hours_at_last_service"]
        assert hours_since > brg["service_interval_hours"], (
            f"BRG-1047 hours_since_service ({hours_since}) is NOT greater than "
            f"service_interval ({brg['service_interval_hours']}) — overdue scenario broken"
        )


# ===========================================================================
# Sensor data
# ===========================================================================
class TestLoadSensorData:
    def test_returns_dataframe(self, prepared):
        assert isinstance(prepared.sensors, pd.DataFrame)

    def test_required_columns_present(self, prepared):
        required = [
            "sensor_id", "asset_id", "component_id",
            "timestamp", "sensor_type", "value",
        ]
        for col in required:
            assert col in prepared.sensors.columns, f"Missing column: {col}"

    def test_sensor_types_valid(self, prepared):
        invalid = ~prepared.sensors["sensor_type"].isin(ALLOWED_SENSOR_TYPES)
        assert not invalid.any(), (
            f"Invalid sensor_type(s): "
            f"{prepared.sensors.loc[invalid, 'sensor_type'].unique()}"
        )

    def test_timestamps_are_datetime(self, prepared):
        assert pd.api.types.is_datetime64_any_dtype(prepared.sensors["timestamp"])

    def test_no_null_timestamps(self, prepared):
        assert prepared.sensors["timestamp"].notna().all()

    def test_no_null_values(self, prepared):
        assert prepared.sensors["value"].notna().all()

    def test_values_are_finite(self, prepared):
        import numpy as np
        assert np.isfinite(prepared.sensors["value"].values).all()

    def test_sorted_chronologically_per_group(self, prepared):
        """
        For every (asset_id, component_id, sensor_type) group, timestamps
        must be non-decreasing.
        """
        groups = prepared.sensors.groupby(
            ["asset_id", "component_id", "sensor_type"]
        )
        for name, grp in groups:
            ts = grp["timestamp"].values
            assert (ts[:-1] <= ts[1:]).all(), (
                f"Group {name} is not chronologically sorted"
            )

    def test_as1047_sensor_readings_present(self, prepared):
        """AS-1047 / BRG-1047 must have all four sensor types."""
        grp = prepared.sensors[
            (prepared.sensors["asset_id"] == "AS-1047") &
            (prepared.sensors["component_id"] == "BRG-1047")
        ]
        found_types = set(grp["sensor_type"].unique())
        assert found_types == ALLOWED_SENSOR_TYPES, (
            f"Expected sensor types {ALLOWED_SENSOR_TYPES}, got {found_types}"
        )

    def test_as1047_vibration_count(self, prepared):
        """Exactly 200 vibration readings for AS-1047 / BRG-1047."""
        vib = prepared.sensors[
            (prepared.sensors["asset_id"] == "AS-1047") &
            (prepared.sensors["component_id"] == "BRG-1047") &
            (prepared.sensors["sensor_type"] == "vibration")
        ]
        assert len(vib) == 200, f"Expected 200 vibration rows, got {len(vib)}"

    def test_as1047_vibration_chronological(self, prepared):
        """AS-1047 vibration readings must be in time order."""
        vib = prepared.sensors[
            (prepared.sensors["asset_id"] == "AS-1047") &
            (prepared.sensors["component_id"] == "BRG-1047") &
            (prepared.sensors["sensor_type"] == "vibration")
        ].reset_index(drop=True)
        ts = vib["timestamp"].values
        assert (ts[:-1] <= ts[1:]).all(), \
            "AS-1047 vibration readings are not chronologically sorted"

    def test_as1047_vibration_degradation_pattern(self, prepared):
        """
        The first 150 vibration readings should average near baseline (~1.5),
        and the last 50 should be significantly higher (degradation signal).
        This validates the canonical scenario without hardcoding any probability.
        """
        vib = prepared.sensors[
            (prepared.sensors["asset_id"] == "AS-1047") &
            (prepared.sensors["component_id"] == "BRG-1047") &
            (prepared.sensors["sensor_type"] == "vibration")
        ].reset_index(drop=True)

        baseline_mean = vib.iloc[:150]["value"].mean()
        degraded_mean = vib.iloc[150:]["value"].mean()

        assert baseline_mean < 2.0, (
            f"Baseline mean {baseline_mean:.3f} exceeds 2.0 — "
            "normal window is unexpectedly elevated"
        )
        assert degraded_mean > 2.5, (
            f"Degraded mean {degraded_mean:.3f} is below 2.5 — "
            "degradation signal is too weak for model training"
        )
        assert degraded_mean > baseline_mean * 1.5, (
            f"Degradation ratio {degraded_mean / baseline_mean:.2f}x is too small. "
            "Rows 150+ must be clearly anomalous vs rows 0–149."
        )


# ===========================================================================
# Maintenance records
# ===========================================================================
class TestLoadMaintenanceRecords:
    def test_returns_dataframe(self, prepared):
        assert isinstance(prepared.maintenance, pd.DataFrame)

    def test_required_columns_present(self, prepared):
        required = [
            "maintenance_id", "asset_id", "component_id",
            "maintenance_type", "maintenance_date",
            "technician_action", "status", "notes",
        ]
        for col in required:
            assert col in prepared.maintenance.columns, f"Missing column: {col}"

    def test_status_values_valid(self, prepared):
        invalid = ~prepared.maintenance["status"].isin(ALLOWED_MAINT_STATUS)
        assert not invalid.any(), (
            f"Invalid status value(s): "
            f"{prepared.maintenance.loc[invalid, 'status'].unique()}"
        )

    def test_no_duplicate_maintenance_ids(self, prepared):
        assert prepared.maintenance["maintenance_id"].is_unique

    def test_as1047_bearing_overdue_record_exists(self, prepared):
        """
        There must be exactly one OVERDUE record for AS-1047 / BRG-1047.
        This is the maintenance status that triggers the NOT_READY hard rule
        in Member 3's Readiness Engine.
        """
        overdue = prepared.maintenance[
            (prepared.maintenance["asset_id"] == "AS-1047") &
            (prepared.maintenance["component_id"] == "BRG-1047") &
            (prepared.maintenance["status"] == "OVERDUE")
        ]
        assert len(overdue) == 1, (
            f"Expected exactly 1 OVERDUE record for AS-1047/BRG-1047, "
            f"got {len(overdue)}"
        )

    def test_only_as1047_bearing_is_overdue(self, prepared):
        """
        In the synthetic dataset only BRG-1047 (AS-1047) should be OVERDUE.
        All other components are within their service intervals.
        """
        overdue = prepared.maintenance[prepared.maintenance["status"] == "OVERDUE"]
        for _, row in overdue.iterrows():
            assert row["asset_id"] == "AS-1047", (
                f"Unexpected OVERDUE asset: {row['asset_id']} / {row['component_id']}"
            )
            assert row["component_id"] == "BRG-1047", (
                f"Unexpected OVERDUE component: {row['component_id']}"
            )


# ===========================================================================
# Referential integrity
# ===========================================================================
class TestReferentialIntegrity:
    def test_all_component_asset_ids_valid(self, prepared):
        valid = set(prepared.assets["asset_id"])
        orphans = ~prepared.components["asset_id"].isin(valid)
        assert not orphans.any(), (
            f"Orphan asset_id(s) in components: "
            f"{prepared.components.loc[orphans, 'asset_id'].unique()}"
        )

    def test_all_sensor_asset_ids_valid(self, prepared):
        valid = set(prepared.assets["asset_id"])
        orphans = ~prepared.sensors["asset_id"].isin(valid)
        assert not orphans.any(), (
            f"Orphan asset_id(s) in sensors: "
            f"{prepared.sensors.loc[orphans, 'asset_id'].unique()}"
        )

    def test_all_sensor_component_ids_valid(self, prepared):
        valid = set(prepared.components["component_id"])
        orphans = ~prepared.sensors["component_id"].isin(valid)
        assert not orphans.any()

    def test_all_maintenance_asset_ids_valid(self, prepared):
        valid = set(prepared.assets["asset_id"])
        orphans = ~prepared.maintenance["asset_id"].isin(valid)
        assert not orphans.any()

    def test_all_maintenance_component_ids_valid(self, prepared):
        valid = set(prepared.components["component_id"])
        orphans = ~prepared.maintenance["component_id"].isin(valid)
        assert not orphans.any()


# ===========================================================================
# load_and_prepare_data — integration
# ===========================================================================
class TestLoadAndPrepareData:
    def test_returns_prepared_datasets_namedtuple(self, prepared):
        assert isinstance(prepared, PreparedDatasets)

    def test_all_four_fields_present(self, prepared):
        assert prepared.assets is not None
        assert prepared.components is not None
        assert prepared.sensors is not None
        assert prepared.maintenance is not None

    def test_row_counts_reasonable(self, prepared):
        assert len(prepared.assets) == 10
        assert len(prepared.components) >= 21    # 3 for AS-1047 + 2 each for 9 others
        assert len(prepared.sensors) >= 16000    # 200 readings × 4 types × 21 components
        assert len(prepared.maintenance) >= 40   # 2 records per component


# ===========================================================================
# AS-1047 canonical scenario — end-to-end
# ===========================================================================
class TestAS1047CanonicalScenario:
    """
    Verifies the complete AS-1047 story at the data layer.
    These assertions guarantee the synthetic data will produce a high-risk
    prediction from Random Forest and HIGH anomaly from Isolation Forest
    without any hardcoding.
    """

    def test_asset_exists_with_high_operational_hours(self, prepared):
        row = prepared.assets[prepared.assets["asset_id"] == "AS-1047"].iloc[0]
        assert row["operational_hours"] > 2000, \
            "AS-1047 operational_hours should be high (simulating aged asset)"

    def test_bearing_is_high_criticality(self, prepared):
        row = prepared.components[
            prepared.components["component_id"] == "BRG-1047"
        ].iloc[0]
        assert row["criticality"] == "HIGH"

    def test_bearing_overdue_flag_will_be_one(self, prepared):
        """
        The computed hours_since_service > service_interval_hours.
        Feature Engineering will set overdue_flag = 1 for this component.
        """
        row = prepared.components[
            prepared.components["component_id"] == "BRG-1047"
        ].iloc[0]
        hours_since = row["operating_hours"] - row["hours_at_last_service"]
        assert hours_since == pytest.approx(420.0, abs=1.0), \
            f"Expected hours_since_service ~420, got {hours_since}"
        assert hours_since > row["service_interval_hours"], \
            "overdue_flag will be 0 — bearing not actually overdue"

    def test_maintenance_overdue_status_matches(self, prepared):
        overdue = prepared.maintenance[
            (prepared.maintenance["asset_id"] == "AS-1047") &
            (prepared.maintenance["component_id"] == "BRG-1047") &
            (prepared.maintenance["status"] == "OVERDUE")
        ]
        assert len(overdue) == 1

    def test_vibration_shows_clear_degradation(self, prepared):
        vib = prepared.sensors[
            (prepared.sensors["asset_id"] == "AS-1047") &
            (prepared.sensors["component_id"] == "BRG-1047") &
            (prepared.sensors["sensor_type"] == "vibration")
        ].reset_index(drop=True)
        final_value = vib["value"].iloc[-1]
        assert final_value > 3.5, \
            f"Final vibration {final_value:.3f} mm/s — not anomalous enough"

    def test_pressure_remains_normal(self, prepared):
        prs = prepared.sensors[
            (prepared.sensors["asset_id"] == "AS-1047") &
            (prepared.sensors["component_id"] == "BRG-1047") &
            (prepared.sensors["sensor_type"] == "pressure")
        ]
        mean_pressure = prs["value"].mean()
        assert 150 < mean_pressure < 220, \
            f"Pressure mean {mean_pressure:.1f} is outside normal range 150–220 psi"

    def test_rpm_remains_normal(self, prepared):
        rpm = prepared.sensors[
            (prepared.sensors["asset_id"] == "AS-1047") &
            (prepared.sensors["component_id"] == "BRG-1047") &
            (prepared.sensors["sensor_type"] == "RPM")
        ]
        mean_rpm = rpm["value"].mean()
        assert 1800 < mean_rpm < 2700, \
            f"RPM mean {mean_rpm:.1f} is outside normal range 1800–2700"
