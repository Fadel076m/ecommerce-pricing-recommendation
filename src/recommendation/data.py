"""
Chargement des données pour le système de recommandation (Jalon 7).

Espace d'identifiants : RetailRocket (visitor_id / item_id) — c'est la seule
source du projet avec un vrai signal comportemental view/add_to_cart/purchase
(cf. roadmap Jalon 7). Ne jamais fusionner avec customer_id/product_id (UCI) :
ce sont des individus/produits différents (cf. docs/data_dictionary.md).

item_properties_part1/2.csv (~900 Mo cumulés) ne doivent jamais être chargés
avec pandas brut : lecture DuckDB filtrée sur les itemid réellement présents
dans les interactions retenues.
"""
from pathlib import Path
import os
import sys

import duckdb
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw_local"
ITEM_PROPERTIES_FILES = [RAW_DIR / "item_properties_part1.csv", RAW_DIR / "item_properties_part2.csv"]

MIN_INTERACTIONS_PER_VISITOR = 5
MIN_INTERACTIONS_PER_ITEM = 5

EVENT_WEIGHTS = {"view": 1.0, "add_to_cart": 3.0, "purchase": 5.0}


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


def load_filtered_interactions(engine=None) -> pd.DataFrame:
    """Interactions visitor_id x item_id, restreintes aux visiteurs/items avec un
    minimum d'historique (le très long tail à 1-2 interactions n'apporte pas de
    signal exploitable pour évaluer un split temporel — cf. docs/recommendation.md)."""
    engine = engine or get_engine()
    events = pd.read_sql(
        "SELECT visitor_id, item_id, event_type, event_time FROM fact_web_events ORDER BY visitor_id, event_time",
        engine,
        parse_dates=["event_time"],
    )

    visitor_counts = events["visitor_id"].value_counts()
    item_counts = events["item_id"].value_counts()
    kept_visitors = visitor_counts[visitor_counts >= MIN_INTERACTIONS_PER_VISITOR].index
    kept_items = item_counts[item_counts >= MIN_INTERACTIONS_PER_ITEM].index

    filtered = events[events["visitor_id"].isin(kept_visitors) & events["item_id"].isin(kept_items)].copy()
    filtered["weight"] = filtered["event_type"].map(EVENT_WEIGHTS)
    return filtered


def load_item_categories(item_ids) -> pd.DataFrame:
    """categoryid le plus récent par item, lu en filtré depuis item_properties_part1/2.csv
    (DuckDB, jamais pandas brut sur ces fichiers)."""
    for path in ITEM_PROPERTIES_FILES:
        if not path.exists():
            raise FileNotFoundError(
                f"{path} introuvable. Copier item_properties_part1/2.csv depuis "
                "'Projet Ecommerce/data' vers data/raw_local/ (non versionné)."
            )

    con = duckdb.connect()
    # Table temporaire plutôt qu'un IN (...) géant (~90k items) : plus robuste et
    # laisse DuckDB faire un hash-join au lieu de parser une clause monstrueuse.
    wanted_items = pd.DataFrame({"itemid": pd.to_numeric(pd.Series(list(item_ids)), errors="coerce").dropna().astype("int64")})
    con.register("wanted_items", wanted_items)
    files = ", ".join(f"'{p.as_posix()}'" for p in ITEM_PROPERTIES_FILES)
    query = f"""
        WITH filtered AS (
            SELECT p.itemid, p.value, p.timestamp
            FROM read_csv_auto([{files}]) p
            JOIN wanted_items w ON w.itemid = p.itemid
            WHERE p.property = 'categoryid'
        ),
        latest AS (
            SELECT itemid, value AS category_id,
                   ROW_NUMBER() OVER (PARTITION BY itemid ORDER BY timestamp DESC) AS rn
            FROM filtered
        )
        SELECT itemid AS item_id, category_id FROM latest WHERE rn = 1
    """
    df = con.execute(query).df()
    con.close()
    df["item_id"] = df["item_id"].astype(str)
    return df
