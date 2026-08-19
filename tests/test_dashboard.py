"""
Tests des pages du dashboard (Jalon 9) : les fonctions de callback produisent
un arbre de composants Dash valide sans exception, à partir de vraies données
de l'API.

Nécessite l'API accessible (variable d'environnement API_BASE_URL) + les
mêmes artefacts que tests/test_api.py. Skip entier sinon.
"""
from pathlib import Path
import sys

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard.api_client import API_BASE_URL  # noqa: E402

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
REQUIRED_ARTIFACTS = [
    "forecasting_lightgbm_global.txt",
    "forecasting_known_products.parquet",
    "pricing_recommendations.parquet",
    "recommendation_visitor_lookup.parquet",
    "recommendation_popular_items.parquet",
]


def _api_reachable() -> bool:
    try:
        return requests.get(f"{API_BASE_URL}/health", timeout=3).status_code == 200
    except requests.RequestException:
        return False


pytestmark = pytest.mark.skipif(
    not (_api_reachable() and all((MODELS_DIR / f).exists() for f in REQUIRED_ARTIFACTS)),
    reason=f"API inaccessible sur {API_BASE_URL} ou artefacts Jalons 5-7 absents (lancer l'API + `make forecast pricing recommend`).",
)


@pytest.fixture(scope="module")
def dash_app():
    """dash.register_page() exige qu'une app Dash existe déjà — instanciée une
    fois pour tout le module de test (mêmes pages que dashboard/app.py)."""
    from dash import Dash

    pages_folder = str(Path(__file__).resolve().parent.parent / "dashboard" / "pages")
    return Dash(__name__, use_pages=True, pages_folder=pages_folder)


def test_executive_page_loads(dash_app):
    from dashboard.pages import executive

    content = executive.load_executive(None)
    assert content is not None


def test_forecast_page_search_and_load(dash_app):
    from dashboard.pages import forecast

    options = forecast.search_products(None)
    assert isinstance(options, list)
    if options:
        content = forecast.load_forecast(options[0]["value"])
        assert content is not None


def test_forecast_page_no_selection_shows_empty_state(dash_app):
    from dashboard.pages import forecast

    content = forecast.load_forecast(None)
    assert content is not None


def test_pricing_page_search_and_load(dash_app):
    from dashboard.pages import pricing

    options = pricing.search_products(None)
    assert isinstance(options, list)
    if options:
        content = pricing.load_pricing(options[0]["value"])
        assert content is not None


def test_recommendation_page_sample_and_load(dash_app):
    from dashboard.pages import recommendation

    visitors = recommendation.load_sample_visitors(None)
    assert isinstance(visitors, list)
    if visitors:
        content = recommendation.load_recommendations(visitors[0]["value"])
        assert content is not None


def test_inventory_page_loads(dash_app):
    from dashboard.pages import inventory

    content = inventory.load_inventory(None)
    assert content is not None
