"""Baseline Moving Average (Jalon 5) — obligatoire avant tout modèle complexe (AGENTS.md §4)."""
import numpy as np
import pandas as pd


def moving_average_forecast(train: pd.DataFrame, horizon: int, window: int = 7) -> np.ndarray:
    """Prévoit `horizon` jours à venir avec la moyenne mobile des `window` derniers jours de train.
    Constante sur tout l'horizon (une vraie baseline, pas de tendance ni saisonnalité)."""
    last_values = train["y"].tail(window)
    forecast_value = last_values.mean() if len(last_values) > 0 else 0.0
    return np.full(horizon, forecast_value)
