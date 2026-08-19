"""
Pipeline recommendation complet (Jalon 7) : Baseline Most Popular ->
Content-based -> Collaborative filtering -> Hybride, split temporel strict,
métriques Precision@K/Recall@K/MAP@K, logging MLflow.

Usage : python -m src.recommendation.train
"""
from pathlib import Path
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import mlflow
import numpy as np
import pandas as pd
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.recommendation.baseline import most_popular_items, recommend_most_popular  # noqa: E402
from src.recommendation.collaborative import build_faiss_index, build_interaction_matrix, recommend_collaborative, train_svd  # noqa: E402
from src.recommendation.content_based import build_category_item_popularity, recommend_content_based, to_category_item_dict  # noqa: E402
from src.recommendation.data import get_engine, load_filtered_interactions, load_item_categories  # noqa: E402
from src.recommendation.evaluate import evaluate_recommendations, temporal_train_test_split  # noqa: E402
from src.recommendation.hybrid import recommend_hybrid  # noqa: E402

TEST_FRACTION = 0.2
TOP_K = 10
MAX_EVAL_VISITORS = 5000  # scoping : garder l'évaluation tractable dans le temps imparti
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = REPO_ROOT / "models"


def main():
    load_dotenv()
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment("recommendation")

    engine = get_engine()
    interactions = load_filtered_interactions(engine)
    print(f"Interactions filtrées : {len(interactions)} lignes, {interactions['visitor_id'].nunique()} visiteurs, {interactions['item_id'].nunique()} items.")

    train, test, cutoff = temporal_train_test_split(interactions, TEST_FRACTION)
    print(f"Split temporel : cutoff {cutoff}, {len(train)} interactions train, {len(test)} interactions test.")

    train_seen = train.groupby("visitor_id")["item_id"].apply(set)
    test_relevant = test.groupby("visitor_id")["item_id"].apply(set)
    eval_visitors = sorted(set(train_seen.index) & set(test_relevant.index))
    if len(eval_visitors) > MAX_EVAL_VISITORS:
        rng = np.random.default_rng(42)
        eval_visitors = list(rng.choice(eval_visitors, size=MAX_EVAL_VISITORS, replace=False))
    print(f"Visiteurs évalués (présents en train ET test) : {len(eval_visitors)}.")

    item_categories = load_item_categories(interactions["item_id"].unique())
    print(f"Catégories chargées pour {item_categories['item_id'].nunique()} items.")

    popular_items = most_popular_items(train, top_k=200)
    category_popularity = build_category_item_popularity(train, item_categories)
    category_dict = to_category_item_dict(category_popularity)

    matrix, visitor_index, item_index = build_interaction_matrix(train)
    _, visitor_embeddings, item_embeddings = train_svd(matrix)
    faiss_index = build_faiss_index(item_embeddings)
    visitor_position = {v: i for i, v in enumerate(visitor_index)}

    baseline_recs, content_recs, collab_recs, hybrid_recs = {}, {}, {}, {}
    for visitor_id in eval_visitors:
        seen = train_seen.get(visitor_id, set())
        visitor_train_history = train[train["visitor_id"] == visitor_id]

        baseline_recs[visitor_id] = recommend_most_popular(visitor_id, popular_items, seen, k=TOP_K)
        content_recs[visitor_id] = recommend_content_based(visitor_train_history, item_categories, category_dict, seen, k=TOP_K)

        if visitor_id in visitor_position:
            visitor_embedding = visitor_embeddings[visitor_position[visitor_id]]
            collab_recs[visitor_id] = recommend_collaborative(visitor_embedding, faiss_index, item_index, seen, k=TOP_K)
        else:
            collab_recs[visitor_id] = []

        hybrid_recs[visitor_id] = recommend_hybrid(content_recs[visitor_id], collab_recs[visitor_id], k=TOP_K)

    # Ne comparer que sur les visiteurs réellement évalués (échantillonnés ci-dessus) :
    # test_relevant contient tous les visiteurs test, pas seulement l'échantillon.
    eval_relevant = {v: test_relevant[v] for v in eval_visitors}

    results = {
        "baseline_most_popular": evaluate_recommendations(baseline_recs, eval_relevant, k=TOP_K),
        "content_based": evaluate_recommendations(content_recs, eval_relevant, k=TOP_K),
        "collaborative_svd_faiss": evaluate_recommendations(collab_recs, eval_relevant, k=TOP_K),
        "hybrid_rrf": evaluate_recommendations(hybrid_recs, eval_relevant, k=TOP_K),
    }

    for run_name, metrics in results.items():
        with mlflow.start_run(run_name=run_name):
            mlflow.log_params(
                {
                    "test_fraction": TEST_FRACTION,
                    "top_k": TOP_K,
                    "n_eval_visitors": len(eval_visitors),
                    "min_interactions_per_visitor": 5,
                    "min_interactions_per_item": 5,
                }
            )
            mlflow.log_metrics({k: v for k, v in metrics.items() if k != "n_visitors_evaluated"})
            print(f"{run_name} :", metrics)

    MODELS_DIR.mkdir(exist_ok=True)
    pd.DataFrame({"item_id": popular_items}).to_parquet(MODELS_DIR / "recommendation_popular_items.parquet", index=False)
    category_popularity.to_parquet(MODELS_DIR / "recommendation_category_popularity.parquet", index=False)
    np.save(MODELS_DIR / "recommendation_item_embeddings.npy", item_embeddings)
    pd.DataFrame({"item_id": list(item_index)}).to_parquet(MODELS_DIR / "recommendation_item_index.parquet", index=False)

    # Table de correspondance visitor_id -> recommandations hybrides précalculées,
    # pour servir l'API (Jalon 8) sans recalculer un SVD/FAISS à chaque requête.
    # Portée volontairement limitée à l'échantillon évalué ci-dessus (cohérence
    # avec les métriques rapportées) ; tout visitor_id hors de cette table retombe
    # sur la baseline Most Popular côté API (cf. docs/api.md).
    lookup_rows = [
        {"visitor_id": visitor_id, "recommended_items": hybrid_recs[visitor_id]}
        for visitor_id in eval_visitors
        if hybrid_recs[visitor_id]
    ]
    pd.DataFrame(lookup_rows).to_parquet(MODELS_DIR / "recommendation_visitor_lookup.parquet", index=False)

    print(f"Artefacts sauvegardés dans {MODELS_DIR} (non versionnés).")


if __name__ == "__main__":
    main()
