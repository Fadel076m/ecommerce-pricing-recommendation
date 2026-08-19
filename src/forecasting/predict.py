"""
Inférence forecasting pour l'API (Jalon 8) : prévision récursive J+1 à J+7.

Le modèle LightGBM global est évalué en 1 pas en avant à l'entraînement
(cf. src/forecasting/train.py) ; ici, à l'inférence, on applique la prédiction
de récursivement : le J+1 prédit devient une donnée d'entrée (lag) pour
prédire J+2, etc. C'est un choix d'implémentation assumé (documenté dans
docs/forecasting.md) — les erreurs se composent avec l'horizon, un J+7 est
mécaniquement moins fiable qu'un J+1.
"""
from pathlib import Path

import lightgbm as lgb
import pandas as pd

from src.forecasting.baseline import moving_average_forecast
from src.forecasting.features import FEATURE_COLUMNS, LAGS, ROLLING_WINDOWS

MIN_HISTORY_DAYS = max(max(LAGS), max(ROLLING_WINDOWS)) + 1


def load_lightgbm_model(model_path: Path) -> lgb.Booster:
    return lgb.Booster(model_file=str(model_path))


def _build_feature_row(history: pd.Series, target_date: pd.Timestamp, known_product_ids: list, product_id: str) -> pd.DataFrame:
    """known_product_ids doit être la liste ORDONNÉE persistée à l'entraînement
    (forecasting_known_products.parquet) : l'encodage catégoriel LightGBM dépend
    de cet ordre exact, un set ou un ordre différent produirait des prédictions
    silencieusement fausses (mauvaise correspondance code catégorie -> produit)."""
    row = {f"lag_{lag}": history.iloc[-lag] for lag in LAGS}
    for window in ROLLING_WINDOWS:
        row[f"rolling_mean_{window}"] = history.iloc[-window:].mean()
    row["day_of_week"] = target_date.dayofweek
    row["day_of_month"] = target_date.day
    row["month"] = target_date.month
    row["is_weekend"] = int(target_date.dayofweek >= 5)
    row["product_id"] = product_id if product_id in known_product_ids else None
    df = pd.DataFrame([row])
    df["product_id"] = pd.Categorical(df["product_id"], categories=list(known_product_ids))
    return df[FEATURE_COLUMNS]


def forecast_product_demand(
    product_id: str,
    history: pd.DataFrame,
    model: lgb.Booster,
    known_product_ids: set,
    horizon: int = 7,
) -> dict:
    """history : DataFrame ['ds', 'y'] trié par date, jours sans vente déjà remplis à 0
    (cf. src/forecasting/data.py::fill_missing_dates). Retourne le forecast + le
    modèle effectivement utilisé (LightGBM ou fallback baseline)."""
    if len(history) < MIN_HISTORY_DAYS or product_id not in known_product_ids:
        forecast_values = moving_average_forecast(history.rename(columns={"y": "y"}), horizon=horizon, window=7)
        model_used = "baseline_moving_average"
    else:
        series = history["y"].copy()
        last_date = history["ds"].max()
        predictions = []
        for step in range(1, horizon + 1):
            target_date = last_date + pd.Timedelta(days=step)
            feature_row = _build_feature_row(series, target_date, known_product_ids, product_id)
            pred = max(0.0, float(model.predict(feature_row)[0]))
            predictions.append(pred)
            series = pd.concat([series, pd.Series([pred])], ignore_index=True)
        forecast_values = predictions
        model_used = "lightgbm_global"

    last_date = history["ds"].max()
    forecast_dates = [(last_date + pd.Timedelta(days=i)).date().isoformat() for i in range(1, horizon + 1)]
    return {
        "product_id": product_id,
        "model_used": model_used,
        "forecast": [
            {"date": date, "predicted_demand": round(float(value), 2)}
            for date, value in zip(forecast_dates, forecast_values)
        ],
    }
