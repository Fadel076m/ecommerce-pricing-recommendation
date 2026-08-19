"""
Chargement des séries de demande depuis PostgreSQL (Jalon 5).

Deux granularités :
- demande agrégée quotidienne (tous produits confondus) : sert de base à la
  comparaison Baseline / Prophet / LightGBM (Prophet ne gère qu'une série à la fois) ;
- demande quotidienne par produit : sert à entraîner un modèle LightGBM global
  (product_id en feature) capable de répondre à /forecast/{product_id} pour
  n'importe quel produit, sans entraîner un modèle par produit (intraitable
  pour ~4600 produits dans le temps imparti).
"""
from pathlib import Path
import os
import sys

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


def get_engine():
    load_dotenv()
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "ecommerce_dw")
    user = os.environ.get("POSTGRES_USER", "ecommerce")
    password = os.environ.get("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError("POSTGRES_PASSWORD manquant dans .env.")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")


def load_daily_demand_aggregate(engine=None) -> pd.DataFrame:
    """Demande quotidienne totale (tous produits), pour la comparaison de modèles."""
    engine = engine or get_engine()
    query = """
        SELECT d.date AS ds, SUM(fs.quantity) AS y
        FROM fact_sales fs
        JOIN dim_date d ON d.date_id = fs.date_id
        GROUP BY d.date
        ORDER BY d.date
    """
    df = pd.read_sql(query, engine, parse_dates=["ds"])
    return df


def load_daily_demand_by_product(engine=None, min_days_with_sales: int = 30) -> pd.DataFrame:
    """Demande quotidienne par produit, filtrée aux produits avec un historique suffisant.

    min_days_with_sales écarte les produits trop rarement vendus pour qu'une
    prévision ait un sens (bruit pur) — ils restent servis par la baseline
    Moving Average dans l'API plutôt que par le modèle LightGBM global.
    """
    engine = engine or get_engine()
    query = """
        SELECT fs.product_id, d.date AS ds, SUM(fs.quantity) AS y
        FROM fact_sales fs
        JOIN dim_date d ON d.date_id = fs.date_id
        GROUP BY fs.product_id, d.date
        ORDER BY fs.product_id, d.date
    """
    df = pd.read_sql(query, engine, parse_dates=["ds"])
    counts = df.groupby("product_id")["ds"].count()
    kept_products = counts[counts >= min_days_with_sales].index
    return df[df["product_id"].isin(kept_products)].reset_index(drop=True)


def fill_missing_dates(df: pd.DataFrame, date_col: str = "ds", value_col: str = "y", group_col: str | None = None) -> pd.DataFrame:
    """Complète les jours sans vente avec y=0 (nécessaire : un produit non vendu un jour donné
    n'apparaît pas dans fact_sales, mais la demande ce jour-là est bien 0, pas une donnée manquante)."""
    if group_col is None:
        full_range = pd.date_range(df[date_col].min(), df[date_col].max(), freq="D")
        return df.set_index(date_col).reindex(full_range).fillna(0).rename_axis(date_col).reset_index()

    filled = []
    for key, group in df.groupby(group_col):
        full_range = pd.date_range(group[date_col].min(), group[date_col].max(), freq="D")
        g = group.set_index(date_col)[[value_col]].reindex(full_range).fillna(0)
        g[group_col] = key
        filled.append(g.rename_axis(date_col).reset_index())
    return pd.concat(filled, ignore_index=True)
