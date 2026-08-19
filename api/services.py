"""
Services de l'API (Jalon 8) : chargent les artefacts des Jalons 5-7 une seule
fois au démarrage et exposent des fonctions simples pour les routes FastAPI.

Ne recalcule jamais de logique métier ici qui existerait déjà dans
src/forecasting, src/pricing, src/recommendation — l'API consomme ces
modules, elle ne duplique pas leur logique (AGENTS.md §5).
"""
from pathlib import Path

import numpy as np
import pandas as pd

from api.db import get_engine
from src.forecasting.data import fill_missing_dates
from src.forecasting.predict import forecast_product_demand, load_lightgbm_model
from src.pricing.simulate import price_grid, simulate_demand, simulate_margin

REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = REPO_ROOT / "models"


class ForecastingService:
    def __init__(self):
        self.model = load_lightgbm_model(MODELS_DIR / "forecasting_lightgbm_global.txt")
        self.known_product_ids = pd.read_parquet(MODELS_DIR / "forecasting_known_products.parquet")["product_id"].tolist()

    def get_forecast(self, product_id: str, horizon: int = 7) -> dict | None:
        engine = get_engine()
        history = pd.read_sql(
            """
            SELECT d.date AS ds, SUM(fs.quantity) AS y
            FROM fact_sales fs
            JOIN dim_date d ON d.date_id = fs.date_id
            WHERE fs.product_id = %(product_id)s
            GROUP BY d.date ORDER BY d.date
            """,
            engine,
            params={"product_id": product_id},
            parse_dates=["ds"],
        )
        if history.empty:
            return None
        history = fill_missing_dates(history)
        return forecast_product_demand(product_id, history, self.model, self.known_product_ids, horizon=horizon)


class PricingService:
    def __init__(self):
        self.table = pd.read_parquet(MODELS_DIR / "pricing_recommendations.parquet").set_index("product_id", drop=False)

    def get_pricing(self, product_id: str) -> dict | None:
        if product_id not in self.table.index:
            return None
        row = self.table.loc[product_id]
        return {
            "product_id": product_id,
            "current_price": row["current_price"],
            "recommended_price": row["recommended_price"],
            "price_difference": row["price_difference"],
            "estimated_demand": row["estimated_demand_at_recommended_price"],
            "estimated_margin_at_current_price": row["estimated_margin_at_current_price"],
            "estimated_margin_at_recommended_price": row["estimated_margin_at_recommended_price"],
            "elasticity": row["elasticity"],
            "elasticity_is_estimated": bool(row["is_estimated"]),
        }

    def simulate(self, product_id: str, price_min_pct: float, price_max_pct: float, n_points: int) -> dict | None:
        if product_id not in self.table.index:
            return None
        row = self.table.loc[product_id]

        candidates = price_grid(row["current_price"], pct_range=(price_min_pct, price_max_pct), n_points=n_points)
        demand = simulate_demand(candidates, base_price=row["current_price"], base_demand=row["avg_daily_demand"], elasticity=row["elasticity"])
        simulation = simulate_margin(candidates, demand, cost_price=row["cost_price"])

        return {
            "product_id": product_id,
            "elasticity": row["elasticity"],
            "simulation": simulation.round(2).to_dict(orient="records"),
        }


class KpiService:
    """KPIs agrégés (Data Warehouse) pour la Page Executive et la Page Inventory
    du dashboard — résultats OBSERVÉS (CA/marge/commandes réels), sauf le stock
    qui reste une variable synthétique (cf. docs/data_dictionary.md)."""

    def get_summary(self) -> dict:
        engine = get_engine()
        row = pd.read_sql(
            """
            SELECT
                COUNT(DISTINCT order_id) AS orders_total,
                ROUND(SUM(revenue)::numeric, 2) AS revenue_total,
                ROUND(SUM(margin)::numeric, 2) AS margin_total,
                ROUND((SUM(revenue) / NULLIF(COUNT(DISTINCT order_id), 0))::numeric, 2) AS average_order_value
            FROM fact_sales
            """,
            engine,
        ).iloc[0]
        counts = pd.read_sql(
            "SELECT (SELECT COUNT(*) FROM dim_product) AS n_products, (SELECT COUNT(*) FROM dim_customer) AS n_customers",
            engine,
        ).iloc[0]
        return {
            "revenue_total": float(row["revenue_total"]),
            "margin_total": float(row["margin_total"]),
            "orders_total": int(row["orders_total"]),
            "average_order_value": float(row["average_order_value"]),
            "n_products": int(counts["n_products"]),
            "n_customers": int(counts["n_customers"]),
        }

    def get_inventory_risk(self, limit: int = 20) -> list:
        engine = get_engine()
        df = pd.read_sql(
            """
            SELECT
                fi.product_id, dp.product_name, fi.closing_stock,
                ROUND((fi.closing_stock / NULLIF(fs.avg_daily_sales, 0))::numeric, 1) AS days_of_stock_estimated
            FROM fact_inventory fi
            JOIN dim_product dp ON dp.product_id = fi.product_id
            JOIN (
                SELECT product_id, SUM(quantity) / GREATEST(1, (SELECT COUNT(DISTINCT date_id) FROM fact_sales)) AS avg_daily_sales
                FROM fact_sales GROUP BY product_id
            ) fs ON fs.product_id = fi.product_id
            WHERE fi.closing_stock > 0
            ORDER BY days_of_stock_estimated ASC
            LIMIT %(limit)s
            """,
            engine,
            params={"limit": limit},
        )
        return df.to_dict(orient="records")

    def get_products(self, search: str | None = None, limit: int = 20) -> list:
        engine = get_engine()
        query = "SELECT product_id, product_name FROM dim_product"
        params = {}
        if search:
            query += " WHERE product_name ILIKE %(search)s"
            params["search"] = f"%{search}%"
        query += " ORDER BY product_id LIMIT %(limit)s"
        params["limit"] = limit
        df = pd.read_sql(query, engine, params=params)
        return df.to_dict(orient="records")


class RecommendationService:
    def __init__(self):
        lookup = pd.read_parquet(MODELS_DIR / "recommendation_visitor_lookup.parquet")
        self.lookup = dict(zip(lookup["visitor_id"], lookup["recommended_items"]))
        self.popular_items = pd.read_parquet(MODELS_DIR / "recommendation_popular_items.parquet")["item_id"].tolist()

    def get_sample_visitor_ids(self, n: int = 10) -> list:
        """Échantillon de visitor_id connus du modèle (dashboard : dropdown de démo,
        les visitor_id RetailRocket étant des identifiants numériques opaques,
        cf. docs/recommendation.md)."""
        return list(self.lookup.keys())[:n]

    def get_recommendations(self, visitor_id: str, k: int = 10) -> dict:
        if visitor_id in self.lookup:
            items = self.lookup[visitor_id][:k]
            is_fallback = False
            reason = "Recommandation hybride (content-based + collaborative filtering, cf. docs/recommendation.md)"
        else:
            items = self.popular_items[:k]
            is_fallback = True
            reason = "visitor_id inconnu du modèle : fallback Most Popular (cf. docs/recommendation.md)"

        return {
            "customer_id": visitor_id,
            "is_cold_start_fallback": is_fallback,
            "recommendations": [
                {"product_id": str(item_id), "score_rank": rank, "reason": reason}
                for rank, item_id in enumerate(items, start=1)
            ],
        }
