"""
test_irrigation_model.py
Unit tests for the ML irrigation prediction model.
"""

import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/python'))
from irrigation_model import generate_synthetic_dataset, train, predict, FEATURE_COLUMNS


@pytest.fixture(scope="module")
def trained_model():
    df = generate_synthetic_dataset(n_samples=500)
    clf, scaler = train(df, save=False)
    return clf, scaler


class TestSyntheticData:
    def test_dataset_shape(self):
        df = generate_synthetic_dataset(500)
        assert len(df) == 500
        assert "irrigate" in df.columns

    def test_binary_labels(self):
        df = generate_synthetic_dataset(500)
        assert set(df["irrigate"].unique()).issubset({0, 1})

    def test_feature_columns_present(self):
        df = generate_synthetic_dataset(200)
        for col in FEATURE_COLUMNS:
            assert col in df.columns, f"Missing feature: {col}"


class TestTraining:
    def test_model_trains_without_error(self, trained_model):
        clf, scaler = trained_model
        assert clf is not None
        assert scaler is not None

    def test_model_has_feature_importances(self, trained_model):
        clf, _ = trained_model
        assert len(clf.feature_importances_) == len(FEATURE_COLUMNS)


class TestPrediction:
    def test_predict_returns_dict(self, trained_model):
        clf, scaler = trained_model
        features = {
            "soil_moisture_pct": 20.0,
            "temperature_c": 35.0,
            "humidity_pct": 40.0,
            "light_lux": 800.0,
            "ph_value": 6.8,
            "et0_mm_day": 7.0,
            "rain_prob_6h": 0.05,
            "hour_of_day": 8,
            "day_of_week": 2,
            "growth_stage_encoded": 2,
        }
        result = predict(features, clf, scaler)
        assert "irrigate" in result
        assert "confidence" in result
        assert "prob_irrigate" in result

    def test_confidence_is_probability(self, trained_model):
        clf, scaler = trained_model
        features = {col: 0.5 for col in FEATURE_COLUMNS}
        result = predict(features, clf, scaler)
        assert 0.0 <= result["confidence"] <= 1.0
        assert 0.0 <= result["prob_irrigate"] <= 1.0

    def test_dry_soil_predicts_irrigate(self, trained_model):
        clf, scaler = trained_model
        features = {
            "soil_moisture_pct": 8.0,    # Very dry
            "temperature_c": 42.0,
            "humidity_pct": 15.0,
            "light_lux": 950.0,
            "et0_mm_day": 9.0,
            "rain_prob_6h": 0.01,
            "hour_of_day": 7,
            "day_of_week": 1,
            "growth_stage_encoded": 2,
            "ph_value": 7.0,
        }
        result = predict(features, clf, scaler)
        assert result["prob_irrigate"] > 0.4, "Dry soil should lean toward irrigation"
