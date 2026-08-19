"""Baseline Most Popular (Jalon 7) — obligatoire avant modèle complexe (AGENTS.md §4)."""
import pandas as pd


def most_popular_items(train_interactions: pd.DataFrame, top_k: int = 200) -> list:
    """Items les plus populaires (somme des poids d'interaction), toutes recommandations
    identiques pour tout visiteur — la baseline la plus simple possible."""
    popularity = train_interactions.groupby("item_id")["weight"].sum().sort_values(ascending=False)
    return popularity.head(top_k).index.tolist()


def recommend_most_popular(visitor_id, popular_items: list, seen_items: set, k: int = 10) -> list:
    return [item for item in popular_items if item not in seen_items][:k]
