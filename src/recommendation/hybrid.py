"""
Recommandation hybride (Jalon 7) : fusion des classements content-based et
collaborative filtering par Reciprocal Rank Fusion (RRF) — combine deux
classements sans avoir à normaliser des scores d'échelles différentes
(popularité pondérée vs produit scalaire d'embeddings SVD).
"""
RRF_K = 60  # constante standard de la littérature RRF (Cormack et al., 2009)


def reciprocal_rank_fusion(ranked_lists: list[list], k: int = RRF_K) -> list:
    scores = {}
    for ranked_list in ranked_lists:
        for rank, item_id in enumerate(ranked_list):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank + 1)
    return [item_id for item_id, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)]


def recommend_hybrid(content_based_list: list, collaborative_list: list, k: int = 10) -> list:
    fused = reciprocal_rank_fusion([content_based_list, collaborative_list])
    return fused[:k]
