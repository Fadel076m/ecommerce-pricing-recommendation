"""
Split temporel + métriques d'évaluation (Jalon 5).

Split temporel strict, jamais de random train/test split.
"""
import numpy as np
import pandas as pd


def temporal_train_test_split(df: pd.DataFrame, test_days: int, date_col: str = "ds"):
    """Découpe strictement temporelle : les `test_days` derniers jours en test,
    tout le reste en train. Aucune ligne de test n'a de date antérieure à une
    ligne de train (pas de fuite d'information du futur vers le passé)."""
    cutoff = df[date_col].max() - pd.Timedelta(days=test_days - 1)
    train = df[df[date_col] < cutoff].copy()
    test = df[df[date_col] >= cutoff].copy()
    return train, test


def mae(y_true, y_pred) -> float:
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def rmse(y_true, y_pred) -> float:
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


def mape(y_true, y_pred, epsilon: float = 1.0) -> float:
    """MAPE avec epsilon au dénominateur : la demande quotidienne peut être
    proche de 0 (produits peu vendus certains jours), un MAPE brut y exploserait
    ou serait indéfini (division par zéro) — cf. roadmap Jalon 5."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred) / (np.abs(y_true) + epsilon))) * 100


def evaluate_forecast(y_true, y_pred) -> dict:
    return {
        "mae": mae(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "mape": mape(y_true, y_pred),
    }
