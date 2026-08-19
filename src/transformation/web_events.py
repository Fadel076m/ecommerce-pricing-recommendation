"""
Traitement de RetailRocket events.csv (~94 Mo) -> fact_web_events.

events.csv est raisonnable pour pandas (contrairement à item_properties_part1/2,
~900 Mo cumulés) mais on utilise DuckDB par cohérence avec le reste du pipeline et pour rester scalable
si la source RetailRocket réelle (plus volumineuse) est utilisée plus tard.

visitorid/itemid RetailRocket sont un espace d'identifiants indépendant de
customer_id/product_id UCI (cf. docs/data_dictionary.md) — jamais fusionnés.
"""
from pathlib import Path

import duckdb
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_EVENTS_CSV = REPO_ROOT / "data" / "raw_local" / "events.csv"

EVENT_TYPE_MAP = {
    "view": "view",
    "addtocart": "add_to_cart",
    "transaction": "purchase",
}

SESSION_GAP_MINUTES = 30


def build_fact_web_events(path: Path = RAW_EVENTS_CSV) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} introuvable. Copier events.csv depuis 'Projet Ecommerce/data' "
            "vers data/raw_local/ (non versionné)."
        )

    con = duckdb.connect()
    df = con.execute(
        f"""
        SELECT
            visitorid,
            itemid,
            event,
            transactionid,
            to_timestamp(timestamp / 1000.0) AS event_time
        FROM read_csv_auto('{path.as_posix()}')
        """
    ).df()
    con.close()

    df = df[df["event"].isin(EVENT_TYPE_MAP)].copy()
    df["event_type"] = df["event"].map(EVENT_TYPE_MAP)
    df["visitor_id"] = df["visitorid"].astype(str)
    df["item_id"] = df["itemid"].astype(str)
    df = df.sort_values(["visitor_id", "event_time"])

    # Découpage de session : inactivité > 30 min = nouvelle session (RetailRocket ne fournit
    # pas de session_id explicite, cf. docs/data_dictionary.md).
    gap = df.groupby("visitor_id")["event_time"].diff() > pd.Timedelta(minutes=SESSION_GAP_MINUTES)
    session_seq = gap.groupby(df["visitor_id"]).cumsum()
    df["session_id"] = df["visitor_id"] + "_S" + session_seq.astype(int).astype(str)

    # event_id : identifiant positionnel garanti unique. transactionid n'est PAS utilisable tel
    # quel (un même transactionid RetailRocket couvre plusieurs lignes/items pour un même
    # panier), et visitor_id+item_id+timestamp peut se répéter sur des doublons de log.
    df = df.reset_index(drop=True)
    df["event_id"] = "EVT_" + df.index.astype(str)

    return df[["event_id", "visitor_id", "item_id", "session_id", "event_type", "event_time"]]
