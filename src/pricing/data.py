"""Chargement des données prix/demande/coût depuis PostgreSQL (Jalon 6)."""
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


def load_product_price_history(engine=None) -> pd.DataFrame:
    """Historique quotidien prix/quantité par produit (base de l'estimation d'élasticité)."""
    engine = engine or get_engine()
    query = """
        SELECT fs.product_id, d.date AS ds, fs.unit_price, fs.quantity
        FROM fact_sales fs
        JOIN dim_date d ON d.date_id = fs.date_id
        ORDER BY fs.product_id, d.date
    """
    return pd.read_sql(query, engine, parse_dates=["ds"])


def load_product_reference(engine=None) -> pd.DataFrame:
    """cost_price/current_price par produit (dim_product) : point de référence de la simulation."""
    engine = engine or get_engine()
    query = "SELECT product_id, product_name, cost_price, base_price, current_price FROM dim_product"
    return pd.read_sql(query, engine)
