"""
irrigation_model.py
Random Forest classifier to predict irrigation need.
Labels: 0 = No irrigation needed, 1 = Irrigate now
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import logging

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    "soil_moisture_pct",
    "temperature_c",
    "humidity_pct",
    "light_lux",
    "ph_value",
    "et0_mm_day",
    "rain_prob_6h",
    "hour_of_day",
    "day_of_week",
    "growth_stage_encoded",
]

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../models/irrigation_rf_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "../../models/scaler.pkl")


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features for model input."""
    df = df.copy()

    if isinstance(df.index, pd.DatetimeIndex):
        df["hour_of_day"] = df.index.hour
        df["day_of_week"] = df.index.dayofweek
    else:
        df["hour_of_day"] = 12
        df["day_of_week"] = 0

    stage_map = {"initial": 0, "vegetative": 1, "flowering": 2, "ripening": 3}
    if "growth_stage" in df.columns:
        df["growth_stage_encoded"] = df["growth_stage"].map(stage_map).fillna(1)
    else:
        df["growth_stage_encoded"] = 1

    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0

    return df[FEATURE_COLUMNS]


def generate_synthetic_dataset(n_samples: int = 2000) -> pd.DataFrame:
    """
    Generate a synthetic labeled training dataset.
    In production, replace with real historical labeled data.
    """
    np.random.seed(42)

    data = {
        "soil_moisture_pct": np.random.uniform(10, 80, n_samples),
        "temperature_c":     np.random.uniform(18, 42, n_samples),
        "humidity_pct":      np.random.uniform(25, 90, n_samples),
        "light_lux":         np.random.uniform(100, 1000, n_samples),
        "ph_value":          np.random.uniform(5.5, 8.5, n_samples),
        "et0_mm_day":        np.random.uniform(2, 9, n_samples),
        "rain_prob_6h":      np.random.uniform(0, 1, n_samples),
        "hour_of_day":       np.random.randint(0, 24, n_samples),
        "day_of_week":       np.random.randint(0, 7, n_samples),
        "growth_stage_encoded": np.random.randint(0, 4, n_samples),
    }
    df = pd.DataFrame(data)

    # Rule-based label generation (simulates agronomist decisions)
    df["irrigate"] = (
        (df["soil_moisture_pct"] < 35) &
        (df["rain_prob_6h"] < 0.4) &
        (df["et0_mm_day"] > 4) &
        (df["hour_of_day"].between(6, 10) | df["hour_of_day"].between(17, 20))
    ).astype(int)

    # Add noise
    flip_mask = np.random.rand(n_samples) < 0.05
    df.loc[flip_mask, "irrigate"] = 1 - df.loc[flip_mask, "irrigate"]

    return df


def train(df: pd.DataFrame = None, save: bool = True):
    """
    Train the irrigation prediction model.

    Args:
        df: DataFrame with features + 'irrigate' label column
        save: Whether to persist model and scaler to disk

    Returns:
        Trained classifier, scaler
    """
    if df is None:
        logger.info("No data provided — using synthetic dataset")
        df = generate_synthetic_dataset()

    X = df[FEATURE_COLUMNS]
    y = df["irrigate"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=150,
        max_depth=10,
        min_samples_split=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print("\n── Model Evaluation ──────────────────────")
    print(classification_report(y_test, y_pred, target_names=["No Irrigation", "Irrigate"]))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    importances = pd.Series(clf.feature_importances_, index=FEATURE_COLUMNS)
    print("\nTop Feature Importances:")
    print(importances.sort_values(ascending=False).head(6).to_string())

    if save:
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(clf, f)
        with open(SCALER_PATH, "wb") as f:
            pickle.dump(scaler, f)
        logger.info(f"Model saved to {MODEL_PATH}")

    return clf, scaler


def predict(features: dict, clf=None, scaler=None) -> dict:
    """
    Predict whether irrigation is needed.

    Args:
        features: dict with sensor and context values
        clf, scaler: Optional pre-loaded model/scaler

    Returns:
        dict with 'irrigate' (bool) and 'confidence' (float)
    """
    if clf is None or scaler is None:
        with open(MODEL_PATH, "rb") as f:
            clf = pickle.load(f)
        with open(SCALER_PATH, "rb") as f:
            scaler = pickle.load(f)

    row = pd.DataFrame([features])
    row = engineer_features(row)
    X_scaled = scaler.transform(row)

    proba = clf.predict_proba(X_scaled)[0]
    label = clf.predict(X_scaled)[0]

    return {
        "irrigate": bool(label),
        "confidence": float(proba[label]),
        "prob_irrigate": float(proba[1]),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    clf, scaler = train()

    sample_features = {
        "soil_moisture_pct": 22.0,
        "temperature_c": 34.0,
        "humidity_pct": 45.0,
        "light_lux": 750.0,
        "ph_value": 6.8,
        "et0_mm_day": 6.5,
        "rain_prob_6h": 0.1,
        "hour_of_day": 7,
        "day_of_week": 2,
        "growth_stage_encoded": 2,
    }

    result = predict(sample_features, clf, scaler)
    print(f"\nPrediction: {'IRRIGATE NOW' if result['irrigate'] else 'No irrigation needed'}")
    print(f"Confidence: {result['confidence']:.1%}")
    print(f"P(Irrigate): {result['prob_irrigate']:.1%}")
