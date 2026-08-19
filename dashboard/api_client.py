"""
Client HTTP vers l'API FastAPI (Jalon 9). Le dashboard ne recalcule jamais
aucune logique métier — il affiche ce que l'API renvoie (AGENTS.md §5).
"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
TIMEOUT = 10


def _get(path: str, params: dict | None = None):
    response = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=TIMEOUT)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def _post(path: str, json: dict):
    response = requests.post(f"{API_BASE_URL}{path}", json=json, timeout=TIMEOUT)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def get_kpi_summary() -> dict:
    return _get("/kpis/summary")


def get_kpi_inventory(limit: int = 20) -> list:
    return _get("/kpis/inventory", {"limit": limit})


def list_products(search: str | None = None, limit: int = 20) -> list:
    params = {"limit": limit}
    if search:
        params["search"] = search
    return _get("/products", params)


def get_forecast(product_id: str) -> dict | None:
    return _get(f"/forecast/{product_id}")


def get_pricing(product_id: str) -> dict | None:
    return _get(f"/pricing/{product_id}")


def simulate_pricing(product_id: str, price_min_pct: float = -0.3, price_max_pct: float = 0.3, n_points: int = 13) -> dict | None:
    return _post(
        "/pricing/simulate",
        {"product_id": product_id, "price_min_pct": price_min_pct, "price_max_pct": price_max_pct, "n_points": n_points},
    )


def get_sample_visitors(n: int = 10) -> list:
    result = _get("/visitors/sample", {"n": n})
    return result["visitor_ids"] if result else []


def get_recommendations(visitor_id: str) -> dict | None:
    return _get(f"/recommendations/{visitor_id}")
