"""
Collaborative filtering (Jalon 7) : factorisation matricielle implicite
(TruncatedSVD, scikit-learn) sur la matrice visiteur × item pondérée par
event_type (view/add_to_cart/purchase), recherche des plus proches voisins en
produit scalaire via FAISS.
"""
import faiss
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD

N_COMPONENTS = 50
CANDIDATE_POOL = 50  # récupéré via FAISS puis filtré des items déjà vus


def build_interaction_matrix(train_interactions: pd.DataFrame):
    """Matrice creuse visiteur x item (somme des poids). Retourne la matrice +
    les index visitor_id/item_id (position -> id) pour retrouver les identifiants."""
    visitor_cat = train_interactions["visitor_id"].astype("category")
    item_cat = train_interactions["item_id"].astype("category")

    codes = pd.DataFrame(
        {"visitor_code": visitor_cat.cat.codes, "item_code": item_cat.cat.codes, "weight": train_interactions["weight"].values}
    )
    grouped = codes.groupby(["visitor_code", "item_code"], as_index=False)["weight"].sum()

    matrix = csr_matrix(
        (grouped["weight"].values, (grouped["visitor_code"].values, grouped["item_code"].values)),
        shape=(len(visitor_cat.cat.categories), len(item_cat.cat.categories)),
    )
    return matrix, visitor_cat.cat.categories, item_cat.cat.categories


def train_svd(matrix: csr_matrix, n_components: int = N_COMPONENTS):
    n_components = min(n_components, min(matrix.shape) - 1)
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    visitor_embeddings = svd.fit_transform(matrix)
    item_embeddings = svd.components_.T
    return svd, visitor_embeddings, item_embeddings


def build_faiss_index(item_embeddings: np.ndarray) -> "faiss.Index":
    index = faiss.IndexFlatIP(item_embeddings.shape[1])
    index.add(np.ascontiguousarray(item_embeddings.astype("float32")))
    return index


def recommend_collaborative(
    visitor_embedding: np.ndarray,
    faiss_index,
    item_categories_index: pd.Index,
    seen_items: set,
    k: int = 10,
) -> list:
    query = np.ascontiguousarray(visitor_embedding.reshape(1, -1).astype("float32"))
    _, neighbor_positions = faiss_index.search(query, CANDIDATE_POOL)

    recommendations = []
    for pos in neighbor_positions[0]:
        if pos < 0:
            continue
        item_id = item_categories_index[pos]
        if item_id in seen_items:
            continue
        recommendations.append(item_id)
        if len(recommendations) >= k:
            break
    return recommendations
