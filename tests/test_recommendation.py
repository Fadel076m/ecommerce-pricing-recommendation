"""Tests du module recommendation (Jalon 7) : baseline, content-based, collaborative,
hybride, split temporel, métriques Precision@K/Recall@K/MAP@K.

Indépendants de PostgreSQL/DuckDB — DataFrames synthétiques.
"""
from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.recommendation.baseline import most_popular_items, recommend_most_popular  # noqa: E402
from src.recommendation.collaborative import build_interaction_matrix  # noqa: E402
from src.recommendation.content_based import (  # noqa: E402
    build_category_item_popularity,
    recommend_content_based,
    to_category_item_dict,
)
from src.recommendation.evaluate import (  # noqa: E402
    average_precision_at_k,
    precision_at_k,
    recall_at_k,
    temporal_train_test_split,
)
from src.recommendation.hybrid import reciprocal_rank_fusion, recommend_hybrid  # noqa: E402


# --- Split temporel -----------------------------------------------------------


def test_temporal_split_has_no_leakage():
    interactions = pd.DataFrame(
        {
            "visitor_id": ["V1"] * 10,
            "item_id": [f"I{i}" for i in range(10)],
            "event_time": pd.date_range("2024-01-01", periods=10, freq="D"),
            "weight": [1.0] * 10,
        }
    )
    train, test, cutoff = temporal_train_test_split(interactions, test_fraction=0.3)

    assert len(train) + len(test) == len(interactions)
    assert train["event_time"].max() < test["event_time"].min()
    assert (train["event_time"] < cutoff).all()
    assert (test["event_time"] >= cutoff).all()


# --- Métriques ------------------------------------------------------------


def test_precision_recall_perfect_match():
    recommended = ["A", "B", "C"]
    relevant = {"A", "B", "C"}
    assert precision_at_k(recommended, relevant, k=3) == 1.0
    assert recall_at_k(recommended, relevant, k=3) == 1.0


def test_precision_at_k_partial_match():
    recommended = ["A", "X", "B", "Y"]
    relevant = {"A", "B"}
    assert precision_at_k(recommended, relevant, k=4) == pytest.approx(0.5)
    assert recall_at_k(recommended, relevant, k=4) == pytest.approx(1.0)


def test_recall_at_k_with_no_relevant_items_is_zero():
    assert recall_at_k(["A", "B"], set(), k=2) == 0.0


def test_average_precision_rewards_early_hits():
    relevant = {"A", "B"}
    ap_early = average_precision_at_k(["A", "X", "B"], relevant, k=3)
    ap_late = average_precision_at_k(["X", "A", "B"], relevant, k=3)
    assert ap_early > ap_late  # même items pertinents, mais trouvés plus tôt = meilleur AP


# --- Baseline Most Popular --------------------------------------------------


def test_most_popular_items_ranks_by_total_weight():
    # Sommes attendues : A=2.0, B=5.0, C=3.0
    train = pd.DataFrame(
        {
            "item_id": ["A", "A", "B", "C", "C", "C"],
            "weight": [1.0, 1.0, 5.0, 1.0, 1.0, 1.0],
        }
    )
    popular = most_popular_items(train, top_k=3)
    assert popular == ["B", "C", "A"]


def test_recommend_most_popular_excludes_seen_items():
    popular = ["A", "B", "C", "D"]
    result = recommend_most_popular("V1", popular, seen_items={"A", "C"}, k=2)
    assert result == ["B", "D"]


# --- Content-based ----------------------------------------------------------


def test_recommend_content_based_favors_visitor_top_category():
    train_interactions = pd.DataFrame(
        {
            "visitor_id": ["V1", "V1", "V2"],
            "item_id": ["I1", "I2", "I3"],
            "weight": [5.0, 1.0, 1.0],
        }
    )
    item_categories = pd.DataFrame({"item_id": ["I1", "I2", "I3", "I4"], "category_id": ["cat1", "cat2", "cat1", "cat1"]})
    popularity = build_category_item_popularity(train_interactions, item_categories)
    category_dict = to_category_item_dict(popularity)

    visitor_history = train_interactions[train_interactions["visitor_id"] == "V1"]
    recs = recommend_content_based(visitor_history, item_categories, category_dict, seen_items={"I1", "I2"}, k=5)

    assert "I4" in recs  # même catégorie (cat1) que I1, l'item fort du visiteur, jamais vu
    assert "I1" not in recs  # déjà vu


# --- Collaborative (structure de la matrice) --------------------------------


def test_build_interaction_matrix_shape_and_values():
    train = pd.DataFrame(
        {
            "visitor_id": ["V1", "V1", "V2"],
            "item_id": ["I1", "I2", "I1"],
            "weight": [2.0, 1.0, 3.0],
        }
    )
    matrix, visitor_index, item_index = build_interaction_matrix(train)

    assert matrix.shape == (2, 2)
    v1_pos = list(visitor_index).index("V1")
    i1_pos = list(item_index).index("I1")
    assert matrix[v1_pos, i1_pos] == 2.0


# --- Hybride (RRF) -----------------------------------------------------------


def test_reciprocal_rank_fusion_favors_items_ranked_high_in_both_lists():
    content_based = ["A", "B", "C"]
    collaborative = ["B", "A", "D"]
    fused = reciprocal_rank_fusion([content_based, collaborative])
    assert fused[0] in {"A", "B"}  # les deux mieux classés dans les deux listes


def test_recommend_hybrid_respects_k():
    result = recommend_hybrid(["A", "B", "C"], ["D", "E", "F"], k=2)
    assert len(result) == 2
