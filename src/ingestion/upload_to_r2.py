"""
Upload du Data Lake vers Cloudflare R2 (compatible S3, via boto3).

Structure du bucket (brief ISM section 7) :
    raw/        données telles que reçues, simplement converties en Parquet
    processed/  données nettoyées/typées/dédupliquées (modèle en étoile)

Ne jamais uploader les fichiers bruts CSV/XLSX tels quels (quotas R2 free
tier, AGENTS.md §3) : toujours convertir en Parquet et ne garder que les
colonnes utiles.

Usage : python -m src.ingestion.upload_to_r2
"""
from io import BytesIO
from pathlib import Path
import os
import sys

import boto3
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.transformation.star_schema import build_star_schema, load_raw_sales  # noqa: E402
from src.transformation.web_events import build_fact_web_events  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def get_r2_client():
    load_dotenv()
    endpoint = os.environ.get("R2_ENDPOINT_URL")
    access_key = os.environ.get("R2_ACCESS_KEY_ID")
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
    bucket = os.environ.get("R2_BUCKET_NAME")
    if not all([endpoint, access_key, secret_key, bucket]):
        raise RuntimeError(
            "Identifiants R2 manquants dans .env (R2_ENDPOINT_URL/R2_ACCESS_KEY_ID/"
            "R2_SECRET_ACCESS_KEY/R2_BUCKET_NAME). Voir AGENTS.md §3 / README pour la procédure."
        )
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
    )
    return client, bucket


def upload_dataframe(client, bucket: str, df, key: str):
    buffer = BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)
    client.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())
    print(f"Uploadé : s3://{bucket}/{key} ({len(df)} lignes, {buffer.getbuffer().nbytes / 1024:.0f} Ko)")


def upload_raw_layer(client, bucket: str):
    """raw/ : sources converties en Parquet, typage minimal, pas de règle métier."""
    raw_sales = load_raw_sales()
    raw_sales.columns = [c.strip() for c in raw_sales.columns]
    for col in raw_sales.select_dtypes(include="object").columns:
        raw_sales[col] = raw_sales[col].astype(str)
    upload_dataframe(client, bucket, raw_sales, "raw/orders/online_retail_ii.parquet")


def upload_processed_layer(client, bucket: str):
    """processed/ : modèle en étoile nettoyé (docs/data_dictionary.md)."""
    tables = build_star_schema()
    key_by_table = {
        "dim_customer": "processed/customers/dim_customer.parquet",
        "dim_product": "processed/products/dim_product.parquet",
        "dim_date": "processed/dates/dim_date.parquet",
        "dim_promotion": "processed/promotions/dim_promotion.parquet",
        "fact_sales": "processed/sales/fact_sales.parquet",
        "fact_inventory": "processed/inventory/fact_inventory.parquet",
    }
    for name, df in tables.items():
        upload_dataframe(client, bucket, df, key_by_table[name])

    fact_web_events = build_fact_web_events()
    upload_dataframe(client, bucket, fact_web_events, "processed/web_events/fact_web_events.parquet")


def main():
    client, bucket = get_r2_client()
    upload_raw_layer(client, bucket)
    upload_processed_layer(client, bucket)


if __name__ == "__main__":
    main()
