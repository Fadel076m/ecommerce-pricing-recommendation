"""
Construction du modèle en étoile (raw -> processed) à partir des sources
publiques + variables synthétiques (seed=42). Logique partagée entre
scripts/data_generator.py (échantillon Jalon 2) et le pipeline complet
Jalon 3/4 (src/ingestion, src/transformation).

Règles non négociables (AGENTS.md §4) :
- pas de data leakage ;
- closing_stock = opening_stock + stock_in - quantity_sold ;
- variables synthétiques identifiées comme telles (docs/data_dictionary.md).
"""
from pathlib import Path
import random

import pandas as pd

RANDOM_SEED = 42

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_XLSX = REPO_ROOT / "data" / "raw_local" / "online_retail_II.xlsx"


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


def load_raw_sales(path: Path = RAW_XLSX) -> pd.DataFrame:
    """Charge les deux feuilles d'online_retail_II.xlsx et les concatène."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} introuvable. Copier online_retail_II.xlsx depuis "
            "'Projet Ecommerce/data' vers data/raw_local/ (non versionné, cf. AGENTS.md §6)."
        )
    sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl")
    df = pd.concat(sheets.values(), ignore_index=True)
    df.columns = [c.strip() for c in df.columns]
    return df


def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoyage minimal : annulations, quantités/prix invalides, clients manquants."""
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
    df = df[~df["order_id"].str.startswith("C")]  # annulations (InvoiceNo commençant par 'C')
    df = df[df["quantity"] > 0]
    df = df[df["unit_price"] >= 0]
    df = df.dropna(subset=["customer_id"])  # décision documentée : commandes anonymes exclues
    df["customer_id"] = df["customer_id"].astype(int).astype(str).radd("CUST_")
    df = df.drop_duplicates()
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    df["date_id"] = df["invoice_date"].dt.strftime("%Y%m%d").astype(int)
    dropped = before - len(df)
    print(f"Nettoyage : {before} lignes brutes -> {len(df)} lignes valides ({dropped} écartées).")
    return df


def build_dim_customer(sales: pd.DataFrame) -> pd.DataFrame:
    """dim_customer : registration_date proxy = première commande observée (cf. data_dictionary.md)."""
    agg = (
        sales.sort_values("invoice_date")
        .groupby("customer_id")
        .agg(
            registration_date=("invoice_date", "first"),
            country=("country", "first"),
        )
        .reset_index()
    )
    random.seed(RANDOM_SEED)
    agg["age"] = [random.randint(18, 75) for _ in range(len(agg))]
    agg["gender"] = [random.choice(["M", "F", "Autre"]) for _ in range(len(agg))]
    agg = agg.rename(columns={"country": "city"})  # approximation documentée : granularité pays, pas ville
    return agg[["customer_id", "age", "gender", "city", "registration_date"]]


def build_dim_product(sales: pd.DataFrame) -> pd.DataFrame:
    """dim_product : base_price/current_price observés, cost_price synthétique (seed=42)."""
    agg = (
        sales.sort_values("invoice_date")
        .groupby("product_id")
        .agg(
            product_name=("product_name", "first"),
            base_price=("unit_price", "median"),
            current_price=("unit_price", "last"),
        )
        .reset_index()
    )
    random.seed(RANDOM_SEED)
    agg["cost_price"] = agg["base_price"].apply(generate_cost_price)
    return agg


def build_fact_inventory(sales: pd.DataFrame, dim_product: pd.DataFrame) -> pd.DataFrame:
    """fact_inventory synthétique (seed=42), calibré sur les ventes moyennes observées par produit.

    Simplification MVP assumée (docs/data_dictionary.md) : un instantané de stock par produit
    (date_id = dernière date observée dans les ventes), pas une série temporelle quotidienne
    complète — suffisant pour le calcul de risque de rupture/surstock du dashboard.
    """
    span_days = max(1, (sales["invoice_date"].max() - sales["invoice_date"].min()).days)
    total_qty = sales.groupby("product_id")["quantity"].sum()
    avg_daily_sales = (total_qty / span_days).reindex(dim_product["product_id"]).fillna(0.1)
    snapshot_date_id = int(sales["invoice_date"].max().strftime("%Y%m%d"))

    random.seed(RANDOM_SEED)
    rows = []
    for product_id, avg_sales in avg_daily_sales.items():
        movement = generate_stock_movement(max(avg_sales, 0.1))
        rows.append({"product_id": product_id, "date_id": snapshot_date_id, **movement})
    return pd.DataFrame(rows)


def build_dim_promotion(dim_product: pd.DataFrame, sales: pd.DataFrame) -> pd.DataFrame:
    """dim_promotion synthétique (seed=42) : un tirage de remise + fenêtre temporelle par produit."""
    period_start = sales["invoice_date"].min()
    period_end = sales["invoice_date"].max()
    span_days = max(1, (period_end - period_start).days)

    random.seed(RANDOM_SEED)
    rows = []
    for i, product_id in enumerate(dim_product["product_id"]):
        discount = generate_promotion()
        if discount > 0:
            offset_days = random.randint(0, span_days - 1)
            duration_days = random.randint(3, 14)
            start_date = period_start + pd.Timedelta(days=offset_days)
            end_date = min(start_date + pd.Timedelta(days=duration_days), period_end)
            rows.append(
                {
                    "promotion_id": f"PROMO_{i:06d}",
                    "product_id": product_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "discount_percentage": discount,
                }
            )
    return pd.DataFrame(rows)


def build_fact_sales(sales: pd.DataFrame, dim_product: pd.DataFrame, dim_promotion: pd.DataFrame) -> pd.DataFrame:
    """fact_sales enrichi : discount/revenue/cost/margin dérivés (AGENTS.md §4)."""
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


def build_dim_date(sales: pd.DataFrame) -> pd.DataFrame:
    """dim_date : une ligne par date calendaire couverte par les ventes observées."""
    dates = pd.date_range(sales["invoice_date"].min().normalize(), sales["invoice_date"].max().normalize(), freq="D")
    dim_date = pd.DataFrame({"date": dates})
    dim_date["date_id"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["day"] = dim_date["date"].dt.day
    dim_date["weekday"] = dim_date["date"].dt.weekday
    dim_date["is_weekend"] = dim_date["weekday"] >= 5
    return dim_date[["date_id", "date", "year", "month", "day", "weekday", "is_weekend"]]


def build_star_schema(raw_xlsx_path: Path = RAW_XLSX) -> dict:
    """Pipeline complet raw -> processed. Retourne un dict {nom_table: DataFrame}."""
    raw = load_raw_sales(raw_xlsx_path)
    sales = clean_sales(raw)
    dim_customer = build_dim_customer(sales)
    dim_product = build_dim_product(sales)
    dim_date = build_dim_date(sales)
    fact_inventory = build_fact_inventory(sales, dim_product)
    dim_promotion = build_dim_promotion(dim_product, sales)
    fact_sales = build_fact_sales(sales, dim_product, dim_promotion)
    return {
        "dim_customer": dim_customer,
        "dim_product": dim_product,
        "dim_date": dim_date,
        "dim_promotion": dim_promotion,
        "fact_sales": fact_sales,
        "fact_inventory": fact_inventory,
    }
