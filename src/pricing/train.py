"""
Pipeline pricing complet (Jalon 6) : élasticité -> simulation -> recommandation,
pour tous les produits, loggé dans MLflow.

Usage : python -m src.pricing.train
"""
from pathlib import Path
import os
import sys

if sys.platform == "win32":
    # MLflow imprime des emojis sur stdout, cp1252 (console Windows) plante dessus
    # même après un run réussi (cf. .claude/memory/learnings.md LRN-008).
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import mlflow
import pandas as pd
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.pricing.data import get_engine, load_product_price_history, load_product_reference  # noqa: E402
from src.pricing.elasticity import estimate_elasticity_for_all_products  # noqa: E402
from src.pricing.simulate import recommend_price  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = REPO_ROOT / "models"


def build_pricing_table(engine) -> pd.DataFrame:
    price_history = load_product_price_history(engine)
    reference = load_product_reference(engine)
    elasticities = estimate_elasticity_for_all_products(price_history)

    avg_daily_demand = (
        price_history.groupby(["product_id", "ds"])["quantity"].sum().reset_index().groupby("product_id")["quantity"].mean()
    )

    merged = reference.merge(elasticities, on="product_id", how="left")
    merged["avg_daily_demand"] = merged["product_id"].map(avg_daily_demand).fillna(0.1)
    merged = merged[merged["avg_daily_demand"] > 0].copy()

    rows = []
    for _, row in merged.iterrows():
        result = recommend_price(
            current_price=row["current_price"],
            base_demand=row["avg_daily_demand"],
            cost_price=row["cost_price"],
            elasticity=row["elasticity"],
        )
        del result["simulation"]
        result["product_id"] = row["product_id"]
        result["is_estimated"] = row["is_estimated"]
        result["r_squared"] = row["r_squared"]
        rows.append(result)

    return pd.DataFrame(rows)


def main():
    load_dotenv()
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment("pricing")

    engine = get_engine()
    pricing_table = build_pricing_table(engine)

    n_estimated = int(pricing_table["is_estimated"].sum())
    n_total = len(pricing_table)
    margin_uplift_pct = (
        (pricing_table["estimated_margin_at_recommended_price"] - pricing_table["estimated_margin_at_current_price"])
        / pricing_table["estimated_margin_at_current_price"].abs().replace(0, pd.NA)
    ) * 100

    with mlflow.start_run(run_name="pricing_simulation_all_products"):
        mlflow.log_params(
            {
                "n_products": n_total,
                "n_products_elasticity_estimated": n_estimated,
                "n_products_elasticity_assumed": n_total - n_estimated,
                "price_grid_pct_range": "-30% / +30%",
                "price_grid_points": 13,
            }
        )
        mlflow.log_metrics(
            {
                "avg_elasticity": float(pricing_table["elasticity"].mean()),
                "median_margin_uplift_pct_estimated": float(margin_uplift_pct.dropna().median()),
                "pct_products_with_price_change_recommended": float((pricing_table["price_difference"] != 0).mean() * 100),
            }
        )

        MODELS_DIR.mkdir(exist_ok=True)
        output_path = MODELS_DIR / "pricing_recommendations.parquet"
        pricing_table.to_parquet(output_path, index=False)
        mlflow.log_artifact(str(output_path))

    print(f"Pricing calculé pour {n_total} produits ({n_estimated} avec élasticité estimée par régression, "
          f"{n_total - n_estimated} avec élasticité assumée par défaut). Résultats -> {output_path}")
    print(pricing_table[["product_id", "current_price", "recommended_price", "elasticity", "is_estimated"]].head(10))


if __name__ == "__main__":
    main()
