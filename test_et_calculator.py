"""
test_et_calculator.py
Unit tests for the Penman-Monteith ET0 calculation module.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/python'))
from et_calculator import SensorData, compute_et0, compute_crop_et, irrigation_deficit


def make_sample_data(**kwargs):
    defaults = dict(
        temperature_c=25.0,
        humidity_pct=60.0,
        wind_speed_ms=2.0,
        solar_radiation=20.0,
        elevation_m=260.0,
        latitude_deg=17.98,
    )
    defaults.update(kwargs)
    return SensorData(**defaults)


class TestComputeET0:
    def test_typical_conditions_positive(self):
        data = make_sample_data()
        et0 = compute_et0(data)
        assert et0 > 0, "ET0 should be positive under normal conditions"

    def test_hot_dry_higher_et0(self):
        hot = make_sample_data(temperature_c=40, humidity_pct=20, wind_speed_ms=4)
        cool = make_sample_data(temperature_c=15, humidity_pct=80, wind_speed_ms=1)
        assert compute_et0(hot) > compute_et0(cool), "Hot/dry should produce higher ET0"

    def test_et0_never_negative(self):
        for temp in [5, 15, 25, 40]:
            data = make_sample_data(temperature_c=temp)
            assert compute_et0(data) >= 0

    def test_et0_typical_range(self):
        data = make_sample_data()
        et0 = compute_et0(data)
        assert 1 < et0 < 15, f"ET0={et0:.2f} outside typical range (1–15 mm/day)"


class TestComputeCropET:
    def test_kc_scaling(self):
        et0 = 5.0
        etc = compute_crop_et(et0, "tomato", "flowering")
        assert abs(etc - et0 * 1.15) < 0.01

    def test_default_crop_fallback(self):
        et0 = 5.0
        etc = compute_crop_et(et0, "unknown_crop", "vegetative")
        assert etc > 0

    def test_all_stages(self):
        for stage in ["initial", "vegetative", "flowering", "ripening"]:
            etc = compute_crop_et(5.0, "tomato", stage)
            assert etc > 0, f"ETc should be positive for stage={stage}"


class TestIrrigationDeficit:
    def test_no_deficit_if_rain_exceeds_etc(self):
        deficit = irrigation_deficit(etc_mm=3.0, rainfall_mm=5.0)
        assert deficit == 0.0

    def test_positive_deficit(self):
        deficit = irrigation_deficit(etc_mm=6.0, rainfall_mm=1.0)
        assert deficit > 0

    def test_efficiency_scaling(self):
        d1 = irrigation_deficit(5.0, 0.0, efficiency=1.0)
        d2 = irrigation_deficit(5.0, 0.0, efficiency=0.5)
        assert d2 > d1, "Lower efficiency requires more water"
