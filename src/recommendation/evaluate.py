"""
Split temporel + métriques Precision@K / Recall@K / MAP@K (Jalon 7).

AGENTS.md §4 : split temporel strict sur les interactions, jamais de split
aléatoire. Coupure globale (même date pour tous les visiteurs) plutôt qu'un
"derniers N% par visiteur" : cohérent avec la méthodologie retenue en
Forecasting/Pricing, et évite qu'un visiteur "voie" indirectement une période
que d'autres visiteurs n'ont pas encore atteinte au moment de la coupure.
"""
import numpy as np
import pandas as pd


def temporal_train_test_split(interactions: pd.DataFrame, test_fraction: float = 0.2):
    cutoff = interactions["event_time"].quantile(1 - test_fraction)
    train = interactions[interactions["event_time"] < cutoff].copy()
    test = interactions[interactions["event_time"] >= cutoff].copy()
    return train, test, cutoff


def precision_at_k(recommended: list, relevant: set, k: int) -> float:
    if k == 0:
        return 0.0
    top_k = recommended[:k]
    hits = sum(1 for item in top_k if item in relevant)
    return hits / k


def recall_at_k(recommended: list, relevant: set, k: int) -> float:
    if not relevant:
        return 0.0
    top_k = recommended[:k]
    hits = sum(1 for item in top_k if item in relevant)
    return hits / len(relevant)


def average_precision_at_k(recommended: list, relevant: set, k: int) -> float:
    if not relevant:
        return 0.0
    top_k = recommended[:k]
    hits = 0
    precisions = []
    for i, item in enumerate(top_k, start=1):
        if item in relevant:
            hits += 1
            precisions.append(hits / i)
    if not precisions:
        return 0.0
    return sum(precisions) / min(len(relevant), k)


def evaluate_recommendations(per_visitor_recommendations: dict, per_visitor_relevant: dict, k: int = 10) -> dict:
    """per_visitor_recommendations / per_visitor_relevant : {visitor_id: [items]/{items}}."""
    precisions, recalls, average_precisions = [], [], []
    for visitor_id, relevant in per_visitor_relevant.items():
        recommended = per_visitor_recommendations.get(visitor_id, [])
        precisions.append(precision_at_k(recommended, relevant, k))
        recalls.append(recall_at_k(recommended, relevant, k))
        average_precisions.append(average_precision_at_k(recommended, relevant, k))

    return {
        f"precision_at_{k}": float(np.mean(precisions)) if precisions else 0.0,
        f"recall_at_{k}": float(np.mean(recalls)) if recalls else 0.0,
        f"map_at_{k}": float(np.mean(average_precisions)) if average_precisions else 0.0,
        "n_visitors_evaluated": len(per_visitor_relevant),
    }
