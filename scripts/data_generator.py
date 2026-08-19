"""
Générateur de variables synthétiques reproductible + échantillon nettoyé.

Charge UCI Online Retail II depuis data/raw_local/online_retail_II.xlsx (non
versionné, copié depuis Projet Ecommerce/data), applique un nettoyage minimal,
génère les variables absentes des sources publiques (cost_price, stock,
promotion, discount — cf. AGENTS.md §3) et exporte un échantillon dans
data/sample/.

Toujours utiliser random.seed(42) pour garantir la reproductibilité (brief
section 15 / AGENTS.md §3). Ces variables synthétiques ne doivent jamais être
présentées comme des données observées (cf. docs/data_dictionary.md).

Usage : python scripts/data_generator.py
"""
from pathlib import Path
import random

import pandas as pd

RANDOM_SEED = 42

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_XLSX = REPO_ROOT / "data" / "raw_local" / "online_retail_II.xlsx"
SAMPLE_DIR = REPO_ROOT / "data" / "sample"

# Taille de l'échantillon exporté (pas le dataset processed complet, qui
# relève du Jalon 3 Data Lake / Jalon 4 Data Warehouse).
SAMPLE_N_ORDERS = 5000


def generate_cost_price(base_price: float, margin_ratio_range=(0.15, 0.45)) -> float:
    """Dérive un cost_price synthétique à partir d'un prix de vente observé."""
    ratio = random.uniform(*margin_ratio_range)
    return round(base_price * (1 - ratio), 2)


def generate_stock_movement(avg_daily_sales: float, days_of_cover_range=(3, 21)):
    """Génère opening_stock / stock_in / closing_stock cohérents pour une période."""
    days_of_cover = random.randint(*days_of_cover_range)
    opening_stock = max(0, round(avg_daily_sales * days_of_cover))
    stock_in = max(0, round(avg_daily_sales * random.uniform(0.5, 1.5)))
    quantity_sold = max(0, round(avg_daily_sales * random.uniform(0.7, 1.3)))
    closing_stock = max(0, opening_stock + stock_in - quantity_sold)
    return {
        "opening_stock": opening_stock,
        "stock_in": stock_in,
        "quantity_sold": quantity_sold,
        "closing_stock": closing_stock,
    }


def generate_promotion(discount_range=(0.05, 0.30), probability=0.15) -> float:
    """Retourne un discount_percentage synthétique, 0 si pas de promotion."""
    if random.random() < probability:
        return round(random.uniform(*discount_range), 2)
    return 0.0


def load_raw_sales() -> pd.DataFrame:
    """Charge les deux feuilles d'online_retail_II.xlsx et les concatène."""
    if not RAW_XLSX.exists():
        raise FileNotFoundError(
            f"{RAW_XLSX} introuvable. Copier online_retail_II.xlsx depuis "
            "'Projet Ecommerce/data' vers data/raw_local/ (non versionné, cf. AGENTS.md §6)."
        )
    sheets = pd.read_excel(RAW_XLSX, sheet_name=None, engine="openpyxl")
    df = pd.concat(sheets.values(), ignore_index=True)
    df.columns = [c.strip() for c in df.columns]
    return df


def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoyage minimal (Jalon 2) : annulations, quantités/prix invalides, clients manquants."""
    df = df.rename(
        columns={
            "Invoice": "order_id",
            "InvoiceNo": "order_id",
            "StockCode": "product_id",
            "Description": "product_name",
            "Quantity": "quantity",
            "InvoiceDate": "invoice_date",
            "Price": "unit_price",
            "UnitPrice": "unit_price",
            "Customer ID": "customer_id",
            "CustomerID": "customer_id",
            "Country": "country",
        }
    )
    df["order_id"] = df["order_id"].astype(str)
    df["product_id"] = df["product_id"].astype(str)
    before = len(df)
    df = df[~df["order_id"].str.startswith("C")]  # annulations (règle brief : InvoiceNo commençant par 'C')
    df = df[df["quantity"] > 0]
    df = df[df["unit_price"] >= 0]
    df = df.dropna(subset=["customer_id"])  # décision documentée : commandes anonymes exclues de l'échantillon
    df["customer_id"] = df["customer_id"].astype(int).astype(str).radd("CUST_")
    df = df.drop_duplicates()
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    df["date_id"] = df["invoice_date"].dt.strftime("%Y%m%d").astype(int)
    dropped = before - len(df)
    print(f"Nettoyage : {before} lignes brutes -> {len(df)} lignes valides ({dropped} écartées).")
    return df


def build_dim_product(sales: pd.DataFrame) -> pd.DataFrame:
    """dim_product : base_price/current_price observés, cost_price synthétique (seed=42)."""
    agg = sales.sort_values("invoice_date").groupby("product_id").agg(
        product_name=("product_name", "first"),
        base_price=("unit_price", "median"),
        current_price=("unit_price", "last"),
    ).reset_index()
    random.seed(RANDOM_SEED)
    agg["cost_price"] = agg["base_price"].apply(generate_cost_price)
    return agg


def build_fact_inventory(sales: pd.DataFrame, dim_product: pd.DataFrame) -> pd.DataFrame:
    """fact_inventory synthétique (seed=42), calibré sur les ventes moyennes observées par produit."""
    span_days = max(1, (sales["invoice_date"].max() - sales["invoice_date"].min()).days)
    total_qty = sales.groupby("product_id")["quantity"].sum()
    avg_daily_sales = (total_qty / span_days).reindex(dim_product["product_id"]).fillna(0.1)

    random.seed(RANDOM_SEED)
    rows = []
    for product_id, avg_sales in avg_daily_sales.items():
        movement = generate_stock_movement(max(avg_sales, 0.1))
        rows.append({"product_id": product_id, **movement})
    return pd.DataFrame(rows)


def build_dim_promotion(dim_product: pd.DataFrame) -> pd.DataFrame:
    """dim_promotion synthétique (seed=42) : un tirage de remise par produit."""
    random.seed(RANDOM_SEED)
    rows = []
    for i, product_id in enumerate(dim_product["product_id"]):
        discount = generate_promotion()
        if discount > 0:
            rows.append(
                {
                    "promotion_id": f"PROMO_{i:06d}",
                    "product_id": product_id,
                    "discount_percentage": discount,
                }
            )
    return pd.DataFrame(rows)


def build_fact_sales(sales: pd.DataFrame, dim_product: pd.DataFrame, dim_promotion: pd.DataFrame) -> pd.DataFrame:
    """fact_sales enrichi : discount/revenue/cost/margin dérivés (AGENTS.md §4 : closing_stock/marge vérifiables)."""
    cost_by_product = dim_product.set_index("product_id")["cost_price"]
    discount_by_product = (
        dim_promotion.set_index("product_id")["discount_percentage"] if not dim_promotion.empty else pd.Series(dtype=float)
    )

    df = sales.copy()
    df["discount"] = df["product_id"].map(discount_by_product).fillna(0.0)
    df["cost_price"] = df["product_id"].map(cost_by_product)
    df["revenue"] = (df["quantity"] * df["unit_price"] * (1 - df["discount"])).round(2)
    df["cost"] = (df["quantity"] * df["cost_price"]).round(2)
    df["margin"] = (df["revenue"] - df["cost"]).round(2)
    return df[
        [
            "order_id",
            "customer_id",
            "product_id",
            "date_id",
            "quantity",
            "unit_price",
            "discount",
            "revenue",
            "cost",
            "margin",
        ]
    ]


def export_sample(fact_sales: pd.DataFrame, dim_product: pd.DataFrame, fact_inventory: pd.DataFrame, dim_promotion: pd.DataFrame):
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    sample_orders = (
        fact_sales["order_id"].drop_duplicates().sample(
            n=min(SAMPLE_N_ORDERS, fact_sales["order_id"].nunique()),
            random_state=RANDOM_SEED,
        )
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
    raw = load_raw_sales()
    sales = clean_sales(raw)
    dim_product = build_dim_product(sales)
    fact_inventory = build_fact_inventory(sales, dim_product)
    dim_promotion = build_dim_promotion(dim_product)
    fact_sales = build_fact_sales(sales, dim_product, dim_promotion)
    export_sample(fact_sales, dim_product, fact_inventory, dim_promotion)


if __name__ == "__main__":
    main()
