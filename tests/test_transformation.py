"""Tests de transformation (Jalon 3/4) : modèle en étoile complet + web events.

Skip si les sources brutes ne sont pas présentes dans data/raw_local/ (non
versionné) — ces tests ne peuvent tourner que sur une machine ayant copié les
fichiers depuis 'Projet Ecommerce/data', cf. AGENTS.md §6.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.transformation.star_schema import RAW_XLSX, build_star_schema  # noqa: E402
from src.transformation.web_events import RAW_EVENTS_CSV, build_fact_web_events  # noqa: E402

pytestmark_sales = pytest.mark.skipif(
    not RAW_XLSX.exists(), reason="online_retail_II.xlsx absent de data/raw_local/ (non versionné)."
)
pytestmark_events = pytest.mark.skipif(
    not RAW_EVENTS_CSV.exists(), reason="events.csv absent de data/raw_local/ (non versionné)."
)


@pytest.fixture(scope="module")
def star_schema_tables():
    return build_star_schema()


@pytestmark_sales
def test_dim_customer_primary_key_is_unique_and_not_null(star_schema_tables):
    dim_customer = star_schema_tables["dim_customer"]
    assert dim_customer["customer_id"].notna().all()
    assert dim_customer["customer_id"].is_unique


@pytestmark_sales
def test_dim_product_primary_key_is_unique_and_prices_non_negative(star_schema_tables):
    dim_product = star_schema_tables["dim_product"]
    assert dim_product["product_id"].notna().all()
    assert dim_product["product_id"].is_unique
    assert (dim_product["cost_price"] >= 0).all()
    assert (dim_product["base_price"] >= 0).all()
    assert (dim_product["current_price"] >= 0).all()


@pytestmark_sales
def test_dim_date_covers_full_period_without_gaps(star_schema_tables):
    dim_date = star_schema_tables["dim_date"]
    assert dim_date["date_id"].is_unique
    assert (dim_date["date"].diff().dropna() == pd_timedelta_one_day()).all()


def pd_timedelta_one_day():
    import pandas as pd

    return pd.Timedelta(days=1)


@pytestmark_sales
def test_fact_sales_business_rules_hold_on_full_dataset(star_schema_tables):
    fact_sales = star_schema_tables["fact_sales"]

    assert fact_sales["customer_id"].notna().all()
    assert fact_sales["product_id"].notna().all()
    assert (fact_sales["quantity"] > 0).all()
    assert (fact_sales["unit_price"] >= 0).all()
    assert (fact_sales["revenue"] >= 0).all()

    expected_revenue = (
        fact_sales["quantity"] * fact_sales["unit_price"] * (1 - fact_sales["discount"])
    ).round(2)
    assert (fact_sales["revenue"] == expected_revenue).all()
    assert (fact_sales["margin"] == (fact_sales["revenue"] - fact_sales["cost"]).round(2)).all()

    # Intégrité référentielle : tout product_id/customer_id de fact_sales existe dans les dimensions.
    assert fact_sales["product_id"].isin(star_schema_tables["dim_product"]["product_id"]).all()
    assert fact_sales["customer_id"].isin(star_schema_tables["dim_customer"]["customer_id"]).all()
    assert fact_sales["date_id"].isin(star_schema_tables["dim_date"]["date_id"]).all()


@pytestmark_sales
def test_fact_inventory_closing_stock_formula_holds_on_full_dataset(star_schema_tables):
    fact_inventory = star_schema_tables["fact_inventory"]

    assert (fact_inventory["opening_stock"] >= 0).all()
    assert (fact_inventory["stock_in"] >= 0).all()
    assert (fact_inventory["closing_stock"] >= 0).all()

    expected_closing = (
        fact_inventory["opening_stock"] + fact_inventory["stock_in"] - fact_inventory["quantity_sold"]
    ).clip(lower=0)
    assert (fact_inventory["closing_stock"] == expected_closing).all()
    assert fact_inventory["product_id"].isin(star_schema_tables["dim_product"]["product_id"]).all()


@pytestmark_sales
def test_dim_promotion_discount_and_dates_are_valid(star_schema_tables):
    dim_promotion = star_schema_tables["dim_promotion"]
    assert (dim_promotion["discount_percentage"] > 0).all()
    assert (dim_promotion["discount_percentage"] <= 0.30).all()
    assert (dim_promotion["start_date"] <= dim_promotion["end_date"]).all()
    assert dim_promotion["product_id"].isin(star_schema_tables["dim_product"]["product_id"]).all()


@pytestmark_events
def test_fact_web_events_event_type_and_ids_are_valid():
    fact_web_events = build_fact_web_events()

    assert fact_web_events["event_type"].isin(["view", "add_to_cart", "purchase"]).all()
    assert fact_web_events["event_id"].notna().all()
    assert fact_web_events["event_id"].is_unique
    assert fact_web_events["visitor_id"].notna().all()
    assert fact_web_events["item_id"].notna().all()
