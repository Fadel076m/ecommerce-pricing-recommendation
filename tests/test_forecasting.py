"""Tests du module forecasting (Jalon 5) : split temporel, métriques, features, baseline.

Ne dépendent pas de PostgreSQL — testés sur des DataFrames synthétiques pour
rester rapides et indépendants de l'état de la base.
"""
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.forecasting.baseline import moving_average_forecast  # noqa: E402
from src.forecasting.evaluate import evaluate_forecast, mae, mape, rmse, temporal_train_test_split  # noqa: E402
from src.forecasting.features import add_time_series_features  # noqa: E402


def test_temporal_split_has_no_leakage():
    df = pd.DataFrame({"ds": pd.date_range("2024-01-01", periods=60, freq="D"), "y": range(60)})
    train, test = temporal_train_test_split(df, test_days=14)

    assert len(train) + len(test) == len(df)
    assert train["ds"].max() < test["ds"].min()
    assert len(test) == 14


def test_evaluate_forecast_perfect_prediction_gives_zero_error():
    y_true = [10, 20, 30, 0]
    metrics = evaluate_forecast(y_true, y_true)
    assert metrics["mae"] == 0
    assert metrics["rmse"] == 0
    assert metrics["mape"] == 0


def test_mape_does_not_explode_near_zero_actuals():
    # Sans epsilon, une vraie valeur de 0 ferait diverger le MAPE (division par zéro).
    value = mape(y_true=[0, 0, 0], y_pred=[1, 2, 0])
    assert np.isfinite(value)
    assert value > 0


def test_mae_rmse_known_values():
    y_true = [10, 10, 10]
    y_pred = [12, 8, 10]
    assert mae(y_true, y_pred) == pytest.approx(4 / 3)
    assert rmse(y_true, y_pred) == pytest.approx(np.sqrt((4 + 4 + 0) / 3))


def test_moving_average_forecast_is_constant_and_uses_recent_window():
    train = pd.DataFrame({"ds": pd.date_range("2024-01-01", periods=10, freq="D"), "y": [0] * 5 + [10] * 5})
    forecast = moving_average_forecast(train, horizon=3, window=5)
    assert len(forecast) == 3
    assert (forecast == 10).all()  # dernière fenêtre de 5 jours = que des 10


def test_add_time_series_features_lags_use_only_past_values():
    df = pd.DataFrame(
        {
            "product_id": ["P1"] * 5,
            "ds": pd.date_range("2024-01-01", periods=5, freq="D"),
            "y": [1, 2, 3, 4, 5],
        }
    )
    features = add_time_series_features(df)

    # lag_1 au jour t doit valoir y(t-1), jamais y(t) ni une valeur future.
    assert features.loc[1, "lag_1"] == 1
    assert features.loc[4, "lag_1"] == 4
    assert pd.isna(features.loc[0, "lag_1"])  # pas de passé pour le tout premier jour


def test_add_time_series_features_does_not_leak_across_products():
    df = pd.DataFrame(
        {
            "product_id": ["P1", "P1", "P2", "P2"],
            "ds": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-02"]),
            "y": [100, 200, 1, 2],
        }
    )
    features = add_time_series_features(df)
    p2_row = features[(features["product_id"] == "P2") & (features["ds"] == "2024-01-02")].iloc[0]
    assert p2_row["lag_1"] == 1  # et surtout pas 200 (valeur de P1)
