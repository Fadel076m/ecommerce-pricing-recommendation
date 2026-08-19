"""
FastAPI — Jalon 8. Endpoints définis dans docs/api.md.

L'API consomme les artefacts des Jalons 5-7 (src/forecasting, src/pricing,
src/recommendation) via api/services.py, elle ne recalcule aucune logique
métier elle-même (AGENTS.md §5 : "le dashboard ne doit pas dupliquer de
logique métier" — même principe appliqué ici à l'API vis-à-vis des modules
d'entraînement).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from api.schemas import (
    ForecastResponse,
    HealthResponse,
    PricingResponse,
    PricingSimulateRequest,
    PricingSimulateResponse,
    RecommendationResponse,
)
from api.services import ForecastingService, PricingService, RecommendationService

_services: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    _services["forecasting"] = ForecastingService()
    _services["pricing"] = PricingService()
    _services["recommendation"] = RecommendationService()
    yield
    _services.clear()


app = FastAPI(
    title="Ecommerce Data-Driven Pricing & Recommandation API",
    description=(
        "Prototype académique — forecasting/pricing/recommendation sous hypothèses "
        "des modèles et de données synthétiques (cost_price/stock/promotion). "
        "Voir docs/forecasting.md, docs/pricing.md, docs/recommendation.md."
    ),
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


@app.get("/forecast/{product_id}", response_model=ForecastResponse)
def get_forecast(product_id: str):
    result = _services["forecasting"].get_forecast(product_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Produit {product_id} introuvable ou sans historique de ventes.")
    return result


@app.get("/pricing/{product_id}", response_model=PricingResponse)
def get_pricing(product_id: str):
    result = _services["pricing"].get_pricing(product_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Produit {product_id} introuvable.")
    return result


@app.post("/pricing/simulate", response_model=PricingSimulateResponse)
def simulate_pricing(request: PricingSimulateRequest):
    result = _services["pricing"].simulate(
        request.product_id, request.price_min_pct, request.price_max_pct, request.n_points
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Produit {request.product_id} introuvable.")
    return result


@app.get("/recommendations/{customer_id}", response_model=RecommendationResponse)
def get_recommendations(customer_id: str):
    return _services["recommendation"].get_recommendations(customer_id)
