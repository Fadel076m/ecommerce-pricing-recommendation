# Recommendation — Jalon 7

## Décision de scope : espace d'identifiants RetailRocket, pas UCI

Le signal comportemental riche (view/add_to_cart/purchase) demandé par la roadmap Jalon 7 **n'existe que dans RetailRocket** (`visitor_id`/`item_id`) — UCI Online Retail II ne contient que des transactions complétées, pas de navigation. Le moteur de recommandation est donc construit **entièrement dans l'espace RetailRocket**.

**Conséquence explicite pour l'API (Jalon 8)** : `GET /recommendations/{customer_id}` documenté dans `docs/api.md` opère en réalité sur un `visitor_id` RetailRocket, pas sur un `customer_id` UCI (`fact_sales`/`dim_customer`) — ces deux espaces d'identifiants ne se recoupent pas et ne sont jamais fusionnés (voir `docs/data_dictionary.md`). C'est une limite structurelle du dataset composite à trois sources publiques indépendantes, pas un bug à corriger : à rappeler dans la documentation de l'API et dans le rapport final.

## Méthodologie

1. **Filtrage** : visiteurs et items avec ≥5 interactions retenus (81 318 visiteurs, 67 625 items, 897 028 interactions sur 2 756 101 événements bruts) — le very-long-tail à 1-2 interactions n'apporte pas de signal exploitable pour un split temporel.
2. **Split temporel strict** : coupure globale à 80 % de la période (14/08/2015), toutes les interactions avant en train, après en test. Testé (`tests/test_recommendation.py::test_temporal_split_has_no_leakage`).
3. **Échantillon d'évaluation** : 5000 visiteurs tirés (seed=42) parmi ceux présents à la fois en train et en test — nécessaire pour garder l'évaluation tractable (81 318 visiteurs × 4 approches aurait été trop long dans le temps imparti).
4. **Quatre approches** (`src/recommendation/`) :
   - **Baseline Most Popular** (`baseline.py`) : items les plus populaires (poids `view=1/add_to_cart=3/purchase=5`), identiques pour tous.
   - **Content-based** (`content_based.py`) : catégorie de chaque item (`item_properties_part1/2.csv`, filtré en DuckDB sur les items retenus — jamais chargé en pandas brut), popularité par catégorie, items jamais interagis inclus avec un poids de base (sinon le content-based perd son intérêt principal : recommander des items froids).
   - **Collaborative filtering** (`collaborative.py`) : TruncatedSVD (scikit-learn, 50 dimensions) sur la matrice creuse visiteur×item pondérée, recherche des voisins par produit scalaire via FAISS.
   - **Hybride** (`hybrid.py`) : fusion Reciprocal Rank Fusion des classements content-based et collaborative.
5. **Métriques** : Precision@10 / Recall@10 / MAP@10, loggées dans MLflow (expérience `recommendation`, 4 runs).

## Résultats (19/08/2026)

| Modèle | Precision@10 | Recall@10 | MAP@10 |
|---|---|---|---|
| Baseline Most Popular | 0,0010 | 0,0024 | 0,0017 |
| Content-based | **0,0057** | **0,0186** | **0,0074** |
| Collaborative (SVD+FAISS) | 0,0016 | 0,0034 | 0,0019 |
| Hybride (RRF) | 0,0043 | 0,0123 | 0,0057 |

**Les trois approches battent la baseline** (critère de validation du jalon rempli). Le content-based domine nettement ce dataset ; le collaborative filtering reste faible en absolu, et l'hybride se situe entre les deux (la fusion RRF est tirée vers le bas par le signal collaboratif plus faible).

## Avertissement sur l'échelle des métriques

Les valeurs absolues (Precision@10 ≈ 0,001-0,006) semblent très basses — c'est **attendu, pas un signe de modèle cassé** : le catalogue compte 67 625 items pour une fenêtre d'observation de ~4,5 mois, avec un signal implicite faible (majoritairement des `view`). **Ce qui compte est la comparaison relative aux autres modèles** (le content-based multiplie la précision de la baseline par ~5,6), pas la valeur absolue — à formuler ainsi dans le rapport, jamais "5,7 recommandations pertinentes sur 1000 sont correctes" présenté sans ce contexte.

## Limites explicites

- Le modèle collaboratif est figé sur le train : un visiteur ou un item apparu seulement après la coupure temporelle (cold-start) ne peut pas être recommandé par cette voie — il retombe sur le content-based/baseline dans l'implémentation actuelle.
- La catégorie d'item (`categoryid` RetailRocket) est le seul attribut produit utilisé pour le content-based ; pas de texte, marque ou prix (RetailRocket ne les fournit pas).
- L'échantillon de 5000 visiteurs évalués est un choix de scope pour tenir le temps du projet, pas l'intégralité de la population éligible (81 318) — les métriques sont une estimation, pas une mesure exhaustive.
