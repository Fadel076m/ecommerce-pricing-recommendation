"""Tests de data quality (brief section 16, docs/data_quality.md).

Deux niveaux :
- tests unitaires sur les fonctions de scripts/data_generator.py (rapides,
  ne dépendent pas des données brutes) ;
- test d'intégration sur l'échantillon data/sample/ (skip si absent, car sa
  génération nécessite online_retail_II.xlsx qui n'est pas versionné).
"""
import random
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.transformation.star_schema import (  # noqa: E402
    RANDOM_SEED,
    generate_cost_price,
    generate_promotion,
    generate_stock_movement,
)

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"


# --- Générateur synthétique : reproductibilité et bornes ---------------------


def test_generate_cost_price_is_reproducible_with_seed():
    random.seed(RANDOM_SEED)
    first_run = [generate_cost_price(100.0) for _ in range(20)]
    random.seed(RANDOM_SEED)
    second_run = [generate_cost_price(100.0) for _ in range(20)]
    assert first_run == second_run


def test_generate_cost_price_stays_below_base_price():
    random.seed(RANDOM_SEED)
    for _ in range(200):
        cost = generate_cost_price(50.0)
        assert 0 < cost < 50.0


def test_generate_stock_movement_respects_closing_stock_formula():
    random.seed(RANDOM_SEED)
    for _ in range(200):
        movement = generate_stock_movement(avg_daily_sales=10.0)
        assert movement["opening_stock"] >= 0
        assert movement["stock_in"] >= 0
        assert movement["quantity_sold"] >= 0
        assert movement["closing_stock"] >= 0
        expected_closing = max(
            0,
            movement["opening_stock"] + movement["stock_in"] - movement["quantity_sold"],
        )
        assert movement["closing_stock"] == expected_closing


def test_generate_promotion_bounds_and_reproducibility():
    random.seed(RANDOM_SEED)
    values = [generate_promotion() for _ in range(500)]
    assert all(v == 0.0 or 0.05 <= v <= 0.30 for v in values)

    random.seed(RANDOM_SEED)
    replay = [generate_promotion() for _ in range(500)]
    assert values == replay


# --- Règles métier (docs/data_quality.md), sur un fixture minimal -----------


@pytest.fixture
def sample_fact_sales():
    return pd.DataFrame(
        {
            "order_id": ["1", "2", "3"],
            "customer_id": ["CUST_1", "CUST_2", "CUST_3"],
            "product_id": ["P1", "P2", "P3"],
            "quantity": [2, 1, 5],
            "unit_price": [10.0, 20.0, 3.0],
            "discount": [0.0, 0.10, 0.0],
            "cost_price": [4.0, 8.0, 1.0],
        }
    )


def test_fact_sales_business_rules(sample_fact_sales):
    df = sample_fact_sales.copy()
    df["revenue"] = df["quantity"] * df["unit_price"] * (1 - df["discount"])
    df["cost"] = df["quantity"] * df["cost_price"]
    df["margin"] = df["revenue"] - df["cost"]

    assert (df["quantity"] > 0).all()
    assert (df["unit_price"] >= 0).all()
    assert (df["revenue"] >= 0).all()
    assert (df["margin"] == df["revenue"] - df["cost"]).all()


def test_dim_customer_id_not_null_and_unique():
    customers = pd.DataFrame({"customer_id": ["CUST_1", "CUST_2", "CUST_3"]})
    assert customers["customer_id"].notna().all()
    assert customers["customer_id"].is_unique


# --- Intégration : échantillon réel (Jalon 2), skip si non généré -----------


@pytest.mark.skipif(
    not (SAMPLE_DIR / "fact_sales_sample.parquet").exists(),
    reason="Échantillon non généré : lancer `python scripts/data_generator.py` d'abord.",
)
def test_sample_fact_sales_respects_business_rules():
    fact_sales = pd.read_parquet(SAMPLE_DIR / "fact_sales_sample.parquet")

    assert fact_sales["product_id"].notna().all()
    assert (fact_sales["quantity"] > 0).all()
    assert (fact_sales["unit_price"] >= 0).all()
    assert (fact_sales["revenue"] >= 0).all()

    expected_revenue = (
        fact_sales["quantity"] * fact_sales["unit_price"] * (1 - fact_sales["discount"])
    ).round(2)
    assert (fact_sales["revenue"] == expected_revenue).all()
    assert (fact_sales["margin"] == (fact_sales["revenue"] - fact_sales["cost"]).round(2)).all()


@pytest.mark.skipif(
    not (SAMPLE_DIR / "dim_product_sample.parquet").exists(),
    reason="Échantillon non généré : lancer `python scripts/data_generator.py` d'abord.",
)
def test_sample_dim_product_prices_are_non_negative():
    dim_product = pd.read_parquet(SAMPLE_DIR / "dim_product_sample.parquet")

    assert dim_product["product_id"].notna().all()
    assert (dim_product["cost_price"] >= 0).all()
    assert (dim_product["base_price"] >= 0).all()
    assert (dim_product["current_price"] >= 0).all()


@pytest.mark.skipif(
    not (SAMPLE_DIR / "fact_inventory_sample.parquet").exists(),
    reason="Échantillon non généré : lancer `python scripts/data_generator.py` d'abord.",
)
def test_sample_fact_inventory_closing_stock_formula():
    fact_inventory = pd.read_parquet(SAMPLE_DIR / "fact_inventory_sample.parquet")

    assert (fact_inventory["opening_stock"] >= 0).all()
    assert (fact_inventory["stock_in"] >= 0).all()
    assert (fact_inventory["closing_stock"] >= 0).all()

    expected_closing = (
        fact_inventory["opening_stock"] + fact_inventory["stock_in"] - fact_inventory["quantity_sold"]
    ).clip(lower=0)
    assert (fact_inventory["closing_stock"] == expected_closing).all()
