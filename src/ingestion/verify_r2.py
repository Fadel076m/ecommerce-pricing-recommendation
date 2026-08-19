"""
Vérification du Data Lake R2 (Jalon 3, critère de validation) : fichiers
uploadés, listés (boto3), lus et analysés (DuckDB).

Usage : python -m src.ingestion.verify_r2
"""
import os

import duckdb
from dotenv import load_dotenv

from src.ingestion.upload_to_r2 import get_r2_client


def list_objects(client, bucket: str):
    print(f"--- Objets dans s3://{bucket} ---")
    paginator = client.get_paginator("list_objects_v2")
    count = 0
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            print(f"  {obj['Key']} ({obj['Size'] / 1024:.0f} Ko)")
            count += 1
    print(f"Total : {count} objets.")
    return count


def duckdb_secret(con, bucket: str):
    load_dotenv()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    endpoint = os.environ["R2_ENDPOINT_URL"].replace("https://", "")
    con.execute(
        f"""
        CREATE OR REPLACE SECRET r2_secret (
            TYPE s3,
            KEY_ID '{os.environ["R2_ACCESS_KEY_ID"]}',
            SECRET '{os.environ["R2_SECRET_ACCESS_KEY"]}',
            ENDPOINT '{endpoint}',
            URL_STYLE 'path',
            REGION 'auto'
        );
        """
    )


def analyze_with_duckdb(bucket: str):
    con = duckdb.connect()
    duckdb_secret(con, bucket)

    print("\n--- fact_sales (processed) : CA / marge / commandes ---")
    print(
        con.execute(
            f"""
            SELECT COUNT(*) AS lignes, COUNT(DISTINCT order_id) AS commandes,
                   ROUND(SUM(revenue), 2) AS ca, ROUND(SUM(margin), 2) AS marge
            FROM read_parquet('s3://{bucket}/processed/sales/fact_sales.parquet')
            """
        ).df()
    )

    print("\n--- fact_web_events (processed) : répartition par type ---")
    print(
        con.execute(
            f"""
            SELECT event_type, COUNT(*) AS n
            FROM read_parquet('s3://{bucket}/processed/web_events/fact_web_events.parquet')
            GROUP BY event_type ORDER BY n DESC
            """
        ).df()
    )

    print("\n--- raw/orders : volumétrie brute ---")
    print(
        con.execute(
            f"SELECT COUNT(*) AS n FROM read_parquet('s3://{bucket}/raw/orders/online_retail_ii.parquet')"
        ).df()
    )
    con.close()


def main():
    client, bucket = get_r2_client()
    n_objects = list_objects(client, bucket)
    if n_objects == 0:
        raise RuntimeError("Bucket vide : lancer d'abord `python -m src.ingestion.upload_to_r2`.")
    analyze_with_duckdb(bucket)


if __name__ == "__main__":
    main()
