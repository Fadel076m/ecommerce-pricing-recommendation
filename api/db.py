"""Connexion PostgreSQL partagée par l'API (Jalon 8)."""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        load_dotenv()
        host = os.environ.get("POSTGRES_HOST", "localhost")
        port = os.environ.get("POSTGRES_PORT", "5432")
        db = os.environ.get("POSTGRES_DB", "ecommerce_dw")
        user = os.environ.get("POSTGRES_USER", "ecommerce")
        password = os.environ.get("POSTGRES_PASSWORD")
        if not password:
            raise RuntimeError("POSTGRES_PASSWORD manquant dans .env.")
        _engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")
    return _engine
