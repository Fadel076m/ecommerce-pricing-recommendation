# API — Endpoints

| Méthode | Route | Description |
|---|---|---|
| GET | /health | Health check |
| GET | /forecast/{product_id} | Prévision de demande J+1 à J+7 |
| GET | /pricing/{product_id} | Prix actuel, prix recommandé, marge estimée |
| GET | /recommendations/{customer_id} | Liste de produits recommandés avec score et raison |
| POST | /pricing/simulate | Simulation de prix sur une plage de valeurs |

Documentation Swagger/OpenAPI générée automatiquement par FastAPI sur `/docs`.
