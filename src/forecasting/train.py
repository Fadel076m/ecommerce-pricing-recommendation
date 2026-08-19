"""
Entraînement + évaluation des modèles de forecasting (Jalon 5).

Baseline Moving Average -> Prophet -> LightGBM (AGENTS.md §4 : baseline
obligatoire avant modèle complexe). Split temporel strict (jamais de random
split). Toutes les expériences sont loggées dans MLflow (AGENTS.md §4).

Usage : python -m src.forecasting.train
"""
from pathlib import Path
import os
import sys

# MLflow imprime des emojis (ex. le run URL) sur stdout : la console Windows par
# défaut (cp1252) ne sait pas les encoder et fait planter le script après un run
# pourtant réussi. On force UTF-8 avant tout import MLflow.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import mlflow
import pandas as pd
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.forecasting.baseline import moving_average_forecast  # noqa: E402
from src.forecasting.data import (  # noqa: E402
    fill_missing_dates,
    get_engine,
    load_daily_demand_aggregate,
    load_daily_demand_by_product,
)
from src.forecasting.evaluate import evaluate_forecast, temporal_train_test_split  # noqa: E402
from src.forecasting.features import FEATURE_COLUMNS, add_time_series_features  # noqa: E402
from src.forecasting.models import build_lightgbm_regressor, predict_lightgbm, predict_prophet, train_prophet  # noqa: E402

TEST_DAYS = 30
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = REPO_ROOT / "models"


def run_aggregate_comparison(engine, mlflow_experiment: str):
    """Baseline vs Prophet sur la demande quotidienne agrégée (Prophet = une série à la fois)."""
    df = load_daily_demand_aggregate(engine)
    df = fill_missing_dates(df)
    train, test = temporal_train_test_split(df, TEST_DAYS)
    print(f"Agrégé : {len(train)} jours train, {len(test)} jours test (cutoff {test['ds'].min().date()}).")

    mlflow.set_experiment(mlflow_experiment)

    with mlflow.start_run(run_name="baseline_moving_average"):
        mlflow.log_params({"window": 7, "test_days": TEST_DAYS, "granularity": "aggregate_daily"})
        forecast = moving_average_forecast(train, horizon=len(test), window=7)
        metrics = evaluate_forecast(test["y"], forecast)
        mlflow.log_metrics(metrics)
        print("Baseline Moving Average :", metrics)

    with mlflow.start_run(run_name="prophet_aggregate"):
        mlflow.log_params({"test_days": TEST_DAYS, "granularity": "aggregate_daily", "weekly_seasonality": True, "yearly_seasonality": True})
        model = train_prophet(train)
        forecast = predict_prophet(model, horizon=len(test))
        metrics = evaluate_forecast(test["y"], forecast)
        mlflow.log_metrics(metrics)
        print("Prophet (agrégé) :", metrics)

    return metrics


def run_lightgbm_global(engine, mlflow_experiment: str):
    """LightGBM global (panel produit x date), évalué en 1 pas en avant (cf. src/forecasting/models.py)."""
    panel = load_daily_demand_by_product(engine, min_days_with_sales=30)
    panel = fill_missing_dates(panel, group_col="product_id")
    print(f"Panel LightGBM : {panel['product_id'].nunique()} produits, {len(panel)} lignes produit-jour.")

    features_df = add_time_series_features(panel)
    features_df = features_df.dropna(subset=[c for c in FEATURE_COLUMNS if c != "product_id"])
    cutoff = features_df["ds"].max() - pd.Timedelta(days=TEST_DAYS - 1)
    train_df = features_df[features_df["ds"] < cutoff].copy()
    test_df = features_df[features_df["ds"] >= cutoff].copy()
    print(f"LightGBM : {len(train_df)} lignes train, {len(test_df)} lignes test.")

    train_df["product_id"] = train_df["product_id"].astype("category")
    test_df["product_id"] = pd.Categorical(test_df["product_id"], categories=train_df["product_id"].cat.categories)

    mlflow.set_experiment(mlflow_experiment)
    with mlflow.start_run(run_name="lightgbm_global"):
        mlflow.log_params(
            {
                "test_days": TEST_DAYS,
                "granularity": "product_daily_one_step_ahead",
                "n_products": panel["product_id"].nunique(),
                "n_estimators": 300,
                "learning_rate": 0.05,
            }
        )
        model = build_lightgbm_regressor()
        model.fit(train_df[FEATURE_COLUMNS], train_df["y"], categorical_feature=["product_id"])

        preds = predict_lightgbm(model, test_df)
        metrics = evaluate_forecast(test_df["y"], preds)
        mlflow.log_metrics(metrics)
        print("LightGBM (global, one-step-ahead) :", metrics)

        MODELS_DIR.mkdir(exist_ok=True)
        model_path = MODELS_DIR / "forecasting_lightgbm_global.txt"
        model.booster_.save_model(str(model_path))
        mlflow.log_artifact(str(model_path))

    return metrics


def main():
    load_dotenv()
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    engine = get_engine()
    run_aggregate_comparison(engine, mlflow_experiment="forecasting")
    run_lightgbm_global(engine, mlflow_experiment="forecasting")


if __name__ == "__main__":
    main()
