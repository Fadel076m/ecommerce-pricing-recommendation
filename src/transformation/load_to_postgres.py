"""
ETL processed -> PostgreSQL (Jalon 4, Data Warehouse).

Applique le DDL (data/schemas/ddl.sql) puis charge le modèle en étoile
construit par src/transformation/star_schema.py et web_events.py.

Usage : python -m src.transformation.load_to_postgres
"""
from pathlib import Path
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.transformation.star_schema import build_star_schema  # noqa: E402
from src.transformation.web_events import build_fact_web_events  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DDL_PATH = REPO_ROOT / "data" / "schemas" / "ddl.sql"


def get_engine():
    load_dotenv()
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "ecommerce_dw")
    user = os.environ.get("POSTGRES_USER", "ecommerce")
    password = os.environ.get("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError("POSTGRES_PASSWORD manquant dans .env.")
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url)


def apply_ddl(engine):
    ddl = DDL_PATH.read_text(encoding="utf-8")
    with engine.begin() as conn:
        for statement in ddl.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
    print("DDL appliqué.")


def load_tables(engine):
    tables = build_star_schema()
    fact_web_events = build_fact_web_events()

    load_order = [
        ("dim_customer", tables["dim_customer"]),
        ("dim_product", tables["dim_product"]),
        ("dim_date", tables["dim_date"]),
        ("dim_promotion", tables["dim_promotion"]),
        ("fact_sales", tables["fact_sales"]),
        ("fact_inventory", tables["fact_inventory"]),
        ("fact_web_events", fact_web_events),
    ]
    for table_name, df in load_order:
        df.to_sql(table_name, engine, if_exists="append", index=False, chunksize=5000, method="multi")
        print(f"Chargé : {table_name} ({len(df)} lignes).")


def main():
    engine = get_engine()
    apply_ddl(engine)
    load_tables(engine)


if __name__ == "__main__":
    main()
