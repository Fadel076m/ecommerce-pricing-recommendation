"""
Simulation de prix (Jalon 6) : courbe de demande à élasticité constante,
plusieurs points de prix testés, sélection du prix qui maximise la marge
estimée.

Résultat d'une simulation, jamais une garantie business —
"sous les hypothèses du modèle et de la simulation".
"""
import numpy as np
import pandas as pd


def price_grid(current_price: float, pct_range: tuple = (-0.30, 0.30), n_points: int = 13) -> np.ndarray:
    """Points de prix candidats autour du prix actuel."""
    pct_steps = np.linspace(pct_range[0], pct_range[1], n_points)
    return current_price * (1 + pct_steps)


def simulate_demand(candidate_prices: np.ndarray, base_price: float, base_demand: float, elasticity: float) -> np.ndarray:
    """Demande simulée à élasticité constante : Q(p) = Q0 * (p / p0) ** elasticity.

    Hypothèse du modèle (à rappeler partout où ce résultat est montré) : la
    demande réagit au prix selon UNE élasticité constante estimée sur
    l'historique — pas un modèle causal, pas de test A/B réel.
    """
    if base_price <= 0 or base_demand <= 0:
        return np.zeros_like(candidate_prices)
    return base_demand * (candidate_prices / base_price) ** elasticity


def simulate_margin(candidate_prices: np.ndarray, demand: np.ndarray, cost_price: float) -> pd.DataFrame:
    revenue = candidate_prices * demand
    cost = cost_price * demand
    margin = revenue - cost
    return pd.DataFrame(
        {
            "price": candidate_prices,
            "estimated_demand": demand,
            "estimated_revenue": revenue,
            "estimated_cost": cost,
            "estimated_margin": margin,
        }
    )


def recommend_price(
    current_price: float,
    base_demand: float,
    cost_price: float,
    elasticity: float,
    pct_range: tuple = (-0.30, 0.30),
    n_points: int = 13,
) -> dict:
    """Simule une grille de prix et retourne le prix qui maximise la marge estimée.

    base_demand : demande quotidienne moyenne observée au prix actuel (point de
    référence de la courbe de demande simulée).
    """
    candidates = price_grid(current_price, pct_range, n_points)
    demand = simulate_demand(candidates, base_price=current_price, base_demand=base_demand, elasticity=elasticity)
    simulation = simulate_margin(candidates, demand, cost_price)

    best_row = simulation.loc[simulation["estimated_margin"].idxmax()]
    current_row = simulation.iloc[(simulation["price"] - current_price).abs().idxmin()]

    return {
        "current_price": round(current_price, 2),
        "recommended_price": round(float(best_row["price"]), 2),
        "price_difference": round(float(best_row["price"] - current_price), 2),
        "estimated_demand_at_recommended_price": round(float(best_row["estimated_demand"]), 2),
        "estimated_margin_at_current_price": round(float(current_row["estimated_margin"]), 2),
        "estimated_margin_at_recommended_price": round(float(best_row["estimated_margin"]), 2),
        "elasticity": round(elasticity, 3),
        "simulation": simulation,
    }
