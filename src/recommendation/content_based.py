"""
Recommandation content-based (Jalon 7) : à partir des catégories des items
consultés/achetés par un visiteur, recommander les items les plus populaires
des mêmes catégories (catégorie = seul attribut produit disponible côté
RetailRocket, `item_properties`, cf. src/recommendation/data.py).
"""
import pandas as pd


def build_category_item_popularity(train_interactions: pd.DataFrame, item_categories: pd.DataFrame) -> pd.DataFrame:
    """Popularité des items au sein de leur catégorie (base du classement content-based).

    Part de TOUS les items catalogués par catégorie (`item_categories`), pas
    seulement ceux déjà présents dans `train_interactions` : c'est justement
    l'intérêt du content-based par rapport au collaborative filtering de pouvoir
    recommander un item jamais interagi (cold-start item), tant qu'il partage sa
    catégorie avec les intérêts connus du visiteur. Un item sans interaction
    reçoit un poids de base non nul pour rester éligible, mais classé derrière
    les items réellement populaires dans la catégorie.
    """
    item_weight = train_interactions.groupby("item_id")["weight"].sum()
    popularity = item_categories.copy()
    popularity["weight"] = popularity["item_id"].map(item_weight).fillna(0.01)
    return popularity.sort_values(["category_id", "weight"], ascending=[True, False])


def to_category_item_dict(category_item_popularity: pd.DataFrame, top_n_per_category: int = 50) -> dict:
    """Convertit la table de popularité en dict {category_id: [(item_id, weight), ...]}
    (déjà trié, tronqué), pour un scoring par visiteur en O(1) lookup plutôt qu'un
    filtre pandas + iterrows répété des milliers de fois pendant l'évaluation."""
    result = {}
    for category_id, group in category_item_popularity.groupby("category_id"):
        result[category_id] = list(zip(group["item_id"].head(top_n_per_category), group["weight"].head(top_n_per_category)))
    return result


def visitor_category_affinity(visitor_train_interactions: pd.DataFrame, item_categories: pd.DataFrame) -> pd.Series:
    """Affinité d'un visiteur pour chaque catégorie = somme des poids d'interaction
    sur les items de cette catégorie, dans son historique d'entraînement."""
    merged = visitor_train_interactions.merge(item_categories, on="item_id", how="inner")
    return merged.groupby("category_id")["weight"].sum().sort_values(ascending=False)


def recommend_content_based(
    visitor_train_interactions: pd.DataFrame,
    item_categories: pd.DataFrame,
    category_item_dict: dict,
    seen_items: set,
    k: int = 10,
) -> list:
    affinity = visitor_category_affinity(visitor_train_interactions, item_categories)
    if affinity.empty:
        return []

    scored_items = {}
    for category_id, category_weight in affinity.items():
        for item_id, item_weight in category_item_dict.get(category_id, []):
            if item_id in seen_items:
                continue
            scored_items[item_id] = scored_items.get(item_id, 0.0) + category_weight * item_weight

    ranked = sorted(scored_items.items(), key=lambda kv: kv[1], reverse=True)
    return [item_id for item_id, _ in ranked[:k]]
