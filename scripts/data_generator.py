"""
Échantillon nettoyé + variables synthétiques pour le développement rapide
(Jalon 2). La logique de construction du modèle en étoile complet vit dans
src/transformation/star_schema.py (réutilisée aussi par le pipeline Jalon 3/4).

Toujours utiliser random.seed(42) pour garantir la reproductibilité (brief
section 15). Les variables synthétiques ne doivent jamais être présentées
comme des données observées (cf. docs/data_dictionary.md).

Usage : python scripts/data_generator.py
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.transformation.star_schema import RANDOM_SEED, build_star_schema  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DIR = REPO_ROOT / "data" / "sample"

# Taille de l'échantillon exporté (pas le dataset processed complet, qui
# relève du Jalon 3 Data Lake / Jalon 4 Data Warehouse).
SAMPLE_N_ORDERS = 5000


def export_sample(fact_sales, dim_product, fact_inventory, dim_promotion):
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    sample_orders = fact_sales["order_id"].drop_duplicates().sample(
        n=min(SAMPLE_N_ORDERS, fact_sales["order_id"].nunique()),
        random_state=RANDOM_SEED,
    )
    fact_sales_sample = fact_sales[fact_sales["order_id"].isin(sample_orders)]
    sample_products = fact_sales_sample["product_id"].unique()

    fact_sales_sample.to_parquet(SAMPLE_DIR / "fact_sales_sample.parquet", index=False)
    dim_product[dim_product["product_id"].isin(sample_products)].to_parquet(
        SAMPLE_DIR / "dim_product_sample.parquet", index=False
    )
    fact_inventory[fact_inventory["product_id"].isin(sample_products)].to_parquet(
        SAMPLE_DIR / "fact_inventory_sample.parquet", index=False
    )
    dim_promotion[dim_promotion["product_id"].isin(sample_products)].to_parquet(
        SAMPLE_DIR / "dim_promotion_sample.parquet", index=False
    )
    print(f"Échantillon exporté dans {SAMPLE_DIR} : {len(fact_sales_sample)} lignes fact_sales, {len(sample_products)} produits.")


def main():
    tables = build_star_schema()
    export_sample(tables["fact_sales"], tables["dim_product"], tables["fact_inventory"], tables["dim_promotion"])


if __name__ == "__main__":
    main()
