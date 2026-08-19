# API — Endpoints

| Méthode | Route | Description |
|---|---|---|
| GET | /health | Health check |
| GET | /forecast/{product_id} | Prévision de demande J+1 à J+7 |
| GET | /pricing/{product_id} | Prix actuel, prix recommandé, marge estimée |
| GET | /recommendations/{customer_id} | Liste de produits recommandés avec score et raison |
| POST | /pricing/simulate | Simulation de prix sur une plage de valeurs |
| GET | /kpis/summary | KPIs globaux observés (CA, marge, commandes, panier moyen, n produits/clients) — Jalon 9, Page Executive |
| GET | /kpis/inventory | Produits les plus à risque de rupture (jours de stock estimés) — Jalon 9, Page Inventory |
| GET | /products | Recherche de produits (id + nom) pour les dropdowns du dashboard |
| GET | /visitors/sample | Échantillon de visitor_id connus du modèle de recommandation, pour démo |

Documentation Swagger/OpenAPI générée automatiquement par FastAPI sur `/docs`.

Les quatre dernières routes existent pour servir le dashboard (Jalon 9) sans qu'il ait besoin de recalculer la moindre agrégation lui-même (AGENTS.md §5).

## Note importante — `/recommendations/{customer_id}` (Jalon 7)

Le moteur de recommandation est entraîné dans l'espace d'identifiants **RetailRocket** (`visitor_id`), pas UCI (`customer_id` de `fact_sales`/`dim_customer`) — ces deux sources ne partagent pas les mêmes individus et ne sont jamais fusionnées (AGENTS.md §3). En pratique, `{customer_id}` sur cette route doit être compris comme un `visitor_id` RetailRocket. À documenter explicitement dans le Swagger et rappeler dans la démo/soutenance — cf. `docs/recommendation.md` pour le détail de cette limite structurelle.
