# API — Endpoints

| Méthode | Route | Description |
|---|---|---|
| GET | /health | Health check |
| GET | /forecast/{product_id} | Prévision de demande J+1 à J+7 |
| GET | /pricing/{product_id} | Prix actuel, prix recommandé, marge estimée |
| GET | /recommendations/{customer_id} | Liste de produits recommandés avec score et raison |
| POST | /pricing/simulate | Simulation de prix sur une plage de valeurs |

Documentation Swagger/OpenAPI générée automatiquement par FastAPI sur `/docs`.

## Note importante — `/recommendations/{customer_id}` (Jalon 7)

Le moteur de recommandation est entraîné dans l'espace d'identifiants **RetailRocket** (`visitor_id`), pas UCI (`customer_id` de `fact_sales`/`dim_customer`) — ces deux sources ne partagent pas les mêmes individus et ne sont jamais fusionnées (AGENTS.md §3). En pratique, `{customer_id}` sur cette route doit être compris comme un `visitor_id` RetailRocket. À documenter explicitement dans le Swagger et rappeler dans la démo/soutenance — cf. `docs/recommendation.md` pour le détail de cette limite structurelle.
