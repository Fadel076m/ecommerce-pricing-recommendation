"""Tests du module pricing (Jalon 6) : élasticité, simulation, recommandation de prix.

Indépendants de PostgreSQL — DataFrames synthétiques construits pour avoir une
élasticité connue, afin de vérifier que la régression la retrouve.
"""
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pricing.elasticity import (  # noqa: E402
    DEFAULT_ASSUMED_ELASTICITY,
    estimate_elasticity,
    is_eligible_for_estimation,
)
from src.pricing.simulate import price_grid, recommend_price, simulate_demand, simulate_margin  # noqa: E402


def _synthetic_log_log_data(true_elasticity: float, n=50, base_price=10.0, base_qty=100.0, seed=42):
    rng = np.random.default_rng(seed)
    prices = base_price * (1 + rng.uniform(-0.4, 0.4, size=n))
    quantities = base_qty * (prices / base_price) ** true_elasticity
    return pd.DataFrame({"unit_price": prices, "quantity": quantities.round().clip(min=0)})


def test_estimate_elasticity_recovers_known_slope_on_synthetic_data():
    df = _synthetic_log_log_data(true_elasticity=-1.8)
    result = estimate_elasticity(df)

    assert result["is_estimated"] is True
    assert result["elasticity"] == pytest.approx(-1.8, abs=0.3)
    assert result["r_squared"] > 0.8


def test_estimate_elasticity_clips_implausible_positive_slope():
    # Bruit pur (pas de vraie relation prix/demande) peut donner une pente positive
    # par hasard sur un petit echantillon : doit etre borne a une valeur <= 0
    # (bien normal), jamais laisse tel quel (inverserait la recommandation de prix).
    rng = np.random.default_rng(7)
    prices = 10.0 * (1 + rng.uniform(-0.3, 0.3, size=30))
    quantities = rng.integers(1, 50, size=30).astype(float)
    df = pd.DataFrame({"unit_price": prices, "quantity": quantities})

    result = estimate_elasticity(df)

    assert result["elasticity"] <= 0
    assert result["elasticity"] >= -10.0


def test_is_eligible_for_estimation_rejects_low_variation_price():
    constant_prices = pd.Series([9.99] * 50)
    assert is_eligible_for_estimation(constant_prices) is False


def test_is_eligible_for_estimation_rejects_too_few_observations():
    varied_but_short = pd.Series([9.0, 10.0, 11.0])
    assert is_eligible_for_estimation(varied_but_short) is False


def test_estimate_elasticity_ignores_zero_prices_without_crashing():
    # log(0) est indéfini : un article offert (prix=0) ne doit pas planter la régression.
    df = _synthetic_log_log_data(true_elasticity=-1.5)
    df = pd.concat([df, pd.DataFrame({"unit_price": [0.0] * 5, "quantity": [3] * 5})], ignore_index=True)

    result = estimate_elasticity(df)

    assert result["is_estimated"] is True
    assert result["elasticity"] == pytest.approx(-1.5, abs=0.3)


def test_estimate_elasticity_falls_back_to_default_when_not_eligible():
    df = pd.DataFrame({"unit_price": [9.99] * 50, "quantity": [10] * 50})
    result = estimate_elasticity(df)

    assert result["is_estimated"] is False
    assert result["elasticity"] == DEFAULT_ASSUMED_ELASTICITY


def test_price_grid_is_centered_on_current_price():
    grid = price_grid(current_price=100.0, pct_range=(-0.2, 0.2), n_points=5)
    assert grid[0] == pytest.approx(80.0)
    assert grid[-1] == pytest.approx(120.0)
    assert grid[2] == pytest.approx(100.0)


def test_simulate_demand_decreases_with_price_for_negative_elasticity():
    prices = np.array([80.0, 100.0, 120.0])
    demand = simulate_demand(prices, base_price=100.0, base_demand=50.0, elasticity=-2.0)
    assert demand[0] > demand[1] > demand[2]  # prix plus bas -> demande plus haute (élasticité négative)
    assert demand[1] == pytest.approx(50.0)  # au prix de référence, demande = demande de référence


def test_simulate_margin_formula():
    prices = np.array([10.0, 20.0])
    demand = np.array([5.0, 3.0])
    result = simulate_margin(prices, demand, cost_price=4.0)

    assert (result["estimated_revenue"] == prices * demand).all()
    assert (result["estimated_cost"] == 4.0 * demand).all()
    assert (result["estimated_margin"] == result["estimated_revenue"] - result["estimated_cost"]).all()


def test_recommend_price_picks_lower_price_when_elastic_and_profitable():
    # Élasticité fortement négative + marge confortable : baisser le prix doit
    # augmenter suffisamment la demande pour que la marge totale progresse.
    result = recommend_price(current_price=20.0, base_demand=100.0, cost_price=2.0, elasticity=-3.0)

    assert result["recommended_price"] < result["current_price"]
    assert result["estimated_margin_at_recommended_price"] >= result["estimated_margin_at_current_price"]


def test_recommend_price_picks_higher_price_when_inelastic():
    # Élasticité proche de 0 (demande peu sensible au prix) : monter le prix
    # doit augmenter la marge sans faire fuir la demande.
    result = recommend_price(current_price=20.0, base_demand=100.0, cost_price=2.0, elasticity=-0.1)

    assert result["recommended_price"] > result["current_price"]
    assert result["estimated_margin_at_recommended_price"] >= result["estimated_margin_at_current_price"]
