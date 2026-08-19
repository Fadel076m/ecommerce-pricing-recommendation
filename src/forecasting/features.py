"""
Feature engineering pour le modèle LightGBM global (Jalon 5).

Un seul modèle est entraîné sur l'ensemble des produits (product_id en feature
catégorielle) plutôt qu'un modèle par produit — intraitable pour ~4600
produits dans le temps imparti, et pattern standard ("global forecasting
model") pour ce type de panel de séries temporelles.

Toutes les features (lags, moyennes mobiles) sont calculées à partir du passé
strict de chaque produit (`shift` avant `rolling`) : aucune fuite d'information
du futur.
"""
import pandas as pd

LAGS = (1, 7, 14)
ROLLING_WINDOWS = (7, 14, 28)


def add_time_series_features(df: pd.DataFrame) -> pd.DataFrame:
    """df doit contenir product_id, ds (date), y — trié par produit puis date."""
    df = df.sort_values(["product_id", "ds"]).reset_index(drop=True)
    grouped = df.groupby("product_id")["y"]

    for lag in LAGS:
        df[f"lag_{lag}"] = grouped.shift(lag)

    for window in ROLLING_WINDOWS:
        df[f"rolling_mean_{window}"] = grouped.shift(1).rolling(window).mean().reset_index(level=0, drop=True)

    df["day_of_week"] = df["ds"].dt.dayofweek
    df["day_of_month"] = df["ds"].dt.day
    df["month"] = df["ds"].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    return df


FEATURE_COLUMNS = (
    [f"lag_{lag}" for lag in LAGS]
    + [f"rolling_mean_{w}" for w in ROLLING_WINDOWS]
    + ["day_of_week", "day_of_month", "month", "is_weekend", "product_id"]
)
