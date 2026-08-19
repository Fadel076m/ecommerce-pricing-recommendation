"""Modèles de forecasting (Jalon 5) : Prophet (série agrégée) et LightGBM (panel global).

Le split temporel train/test se fait en amont, dans src/forecasting/train.py
(les features à base de lags doivent être calculées sur le panel complet
avant de séparer train/test, pour que les premières lignes de test disposent
bien de leur historique — cf. src/forecasting/features.py)."""
import lightgbm as lgb
import pandas as pd
from prophet import Prophet

from src.forecasting.features import FEATURE_COLUMNS


def train_prophet(train: pd.DataFrame) -> Prophet:
    model = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=True)
    model.fit(train[["ds", "y"]])
    return model


def predict_prophet(model: Prophet, horizon: int) -> pd.Series:
    future = model.make_future_dataframe(periods=horizon)
    forecast = model.predict(future)
    return forecast.tail(horizon)["yhat"].clip(lower=0).reset_index(drop=True)


def build_lightgbm_regressor() -> lgb.LGBMRegressor:
    return lgb.LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, random_state=42, verbosity=-1)


def predict_lightgbm(model: lgb.LGBMRegressor, features_df: pd.DataFrame) -> pd.Series:
    preds = model.predict(features_df[FEATURE_COLUMNS])
    return pd.Series(preds, index=features_df.index).clip(lower=0)
