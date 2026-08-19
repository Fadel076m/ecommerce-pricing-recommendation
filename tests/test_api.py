"""
Tests de l'API FastAPI (Jalon 8).

Nécessite Postgres actif (docker-compose) + les artefacts des Jalons 5-7 déjà
générés dans models/ (non versionnés — cf. `make forecast`/`make pricing`/
`make recommend`). Skip entier si les artefacts sont absents, comme pour les
autres tests d'intégration du projet (data_generator, transformation, ...).
"""
from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
REQUIRED_ARTIFACTS = [
    "forecasting_lightgbm_global.txt",
    "forecasting_known_products.parquet",
    "pricing_recommendations.parquet",
    "recommendation_visitor_lookup.parquet",
    "recommendation_popular_items.parquet",
]

pytestmark = pytest.mark.skipif(
    not all((MODELS_DIR / f).exists() for f in REQUIRED_ARTIFACTS),
    reason="Artefacts Jalons 5-7 absents : lancer `make forecast pricing recommend` d'abord.",
)


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def known_product_id():
    return pd.read_parquet(MODELS_DIR / "pricing_recommendations.parquet")["product_id"].iloc[0]


@pytest.fixture(scope="module")
def known_visitor_id():
    return pd.read_parquet(MODELS_DIR / "recommendation_visitor_lookup.parquet")["visitor_id"].iloc[0]


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_forecast_known_product_returns_seven_days(client, known_product_id):
    response = client.get(f"/forecast/{known_product_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["product_id"] == known_product_id
    assert body["model_used"] in {"lightgbm_global", "baseline_moving_average"}
    assert len(body["forecast"]) == 7
    assert all(point["predicted_demand"] >= 0 for point in body["forecast"])


def test_forecast_unknown_product_returns_404(client):
    response = client.get("/forecast/PRODUIT_INEXISTANT_XYZ")
    assert response.status_code == 404


def test_pricing_known_product(client, known_product_id):
    response = client.get(f"/pricing/{known_product_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["product_id"] == known_product_id
    assert body["current_price"] >= 0
    assert body["recommended_price"] >= 0
    assert "elasticity_is_estimated" in body


def test_pricing_unknown_product_returns_404(client):
    response = client.get("/pricing/PRODUIT_INEXISTANT_XYZ")
    assert response.status_code == 404


def test_pricing_simulate(client, known_product_id):
    response = client.post(
        "/pricing/simulate",
        json={"product_id": known_product_id, "price_min_pct": -0.2, "price_max_pct": 0.2, "n_points": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["simulation"]) == 5
    # tolérance abs=0.02 : revenue/cost/margin sont arrondis indépendamment à 2 décimales
    # côté API (lisibilité), la relation exacte margin=revenue-cost ne tient qu'avant arrondi.
    assert all(
        point["estimated_margin"] == pytest.approx(point["estimated_revenue"] - point["estimated_cost"], abs=0.02)
        for point in body["simulation"]
    )


def test_pricing_simulate_unknown_product_returns_404(client):
    response = client.post("/pricing/simulate", json={"product_id": "PRODUIT_INEXISTANT_XYZ"})
    assert response.status_code == 404


def test_recommendations_known_visitor_is_not_fallback(client, known_visitor_id):
    response = client.get(f"/recommendations/{known_visitor_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["is_cold_start_fallback"] is False
    assert len(body["recommendations"]) > 0


def test_recommendations_unknown_visitor_falls_back_to_most_popular(client):
    response = client.get("/recommendations/VISITOR_INCONNU_XYZ")
    assert response.status_code == 200
    body = response.json()
    assert body["is_cold_start_fallback"] is True
    assert len(body["recommendations"]) > 0


# --- Routes support dashboard (Jalon 9) ---------------------------------------


def test_kpi_summary(client):
    response = client.get("/kpis/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["revenue_total"] > 0
    assert body["orders_total"] > 0
    assert body["n_products"] > 0
    assert body["n_customers"] > 0


def test_kpi_inventory_respects_limit(client):
    response = client.get("/kpis/inventory", params={"limit": 5})
    assert response.status_code == 200
    body = response.json()
    assert len(body) <= 5
    assert all(item["closing_stock"] >= 0 for item in body)


def test_products_search(client):
    response = client.get("/products", params={"limit": 5})
    assert response.status_code == 200
    body = response.json()
    assert len(body) <= 5
    assert all("product_id" in p and "product_name" in p for p in body)


def test_visitors_sample(client):
    response = client.get("/visitors/sample", params={"n": 5})
    assert response.status_code == 200
    body = response.json()
    assert len(body["visitor_ids"]) <= 5
