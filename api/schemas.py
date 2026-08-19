"""Schémas Pydantic de l'API (Jalon 8). Champs alignés sur docs/api.md et docs/data_dictionary.md (KPIs)."""
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class ForecastPoint(BaseModel):
    date: str
    predicted_demand: float


class ForecastResponse(BaseModel):
    product_id: str
    model_used: str = Field(description="lightgbm_global ou baseline_moving_average (fallback historique insuffisant)")
    forecast: list[ForecastPoint]
    disclaimer: str = "Prévision sous les hypothèses du modèle — jamais une garantie."


class PricingResponse(BaseModel):
    product_id: str
    current_price: float
    recommended_price: float
    price_difference: float
    estimated_demand: float
    estimated_margin_at_current_price: float
    estimated_margin_at_recommended_price: float
    elasticity: float
    elasticity_is_estimated: bool = Field(description="False = élasticité assumée par défaut, pas mesurée (cf. docs/pricing.md)")
    disclaimer: str = "Résultat de simulation sous hypothèses du modèle — jamais une vérité mesurée."


class PricingSimulateRequest(BaseModel):
    product_id: str
    price_min_pct: float = Field(default=-0.30, description="Borne basse de la grille, en %age du prix actuel")
    price_max_pct: float = Field(default=0.30, description="Borne haute de la grille, en %age du prix actuel")
    n_points: int = Field(default=13, ge=3, le=50)


class PriceSimulationPoint(BaseModel):
    price: float
    estimated_demand: float
    estimated_revenue: float
    estimated_cost: float
    estimated_margin: float


class PricingSimulateResponse(BaseModel):
    product_id: str
    elasticity: float
    simulation: list[PriceSimulationPoint]
    disclaimer: str = "Simulation sous hypothèses du modèle — jamais une vérité mesurée."


class RecommendedItem(BaseModel):
    product_id: str
    score_rank: int
    reason: str


class KpiSummaryResponse(BaseModel):
    revenue_total: float
    margin_total: float
    orders_total: int
    average_order_value: float
    n_products: int
    n_customers: int


class InventoryRiskItem(BaseModel):
    product_id: str
    product_name: str
    closing_stock: int
    days_of_stock_estimated: float | None


class ProductSummary(BaseModel):
    product_id: str
    product_name: str


class SampleVisitorsResponse(BaseModel):
    visitor_ids: list[str]


class RecommendationResponse(BaseModel):
    customer_id: str
    is_cold_start_fallback: bool = Field(description="True = visitor_id inconnu du modèle, recommandations Most Popular")
    recommendations: list[RecommendedItem]
    note: str = (
        "customer_id correspond à un visitor_id RetailRocket, pas un customer_id UCI "
        "(espaces d'identifiants distincts, jamais fusionnés — cf. docs/recommendation.md)."
    )
