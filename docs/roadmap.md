# Roadmap — Jalons datés (deadline dimanche 23/08/2026)

Projet solo. Les 12 jalons du brief ISM sont compressés sur 6 jours, dans l'ordre de priorité imposé par la section 53 du brief ("Priorités en cas de problème") : Fondations → Intelligence → Produit → Industrialisation → Infrastructure avancée (sacrifiable) → Bonus (sacrifiable).

Chaque jalon doit se terminer par un commit git dédié et une mise à jour de la checklist ci-dessous.

## J0 — Mardi 18/08 (reste de journée)

**Objectif** : setup technique prêt à coder.

- [x] Repo initialisé, structure créée
- [x] `.env` rempli localement (jamais commité)
- [x] `docker compose up -d` fonctionnel (Postgres + MLflow)
- [x] Environnement Python créé, `requirements.txt` installé (venv Python 3.12 — 3.14 écarté, wheels prophet/faiss/lightgbm instables dessus ; Airflow isolé dans `requirements-airflow.txt` ; `great_expectations` retiré)
- [x] Démarrage Jalon 1 (cadrage) : problématique, objectifs, périmètre MVP rédigés

## J1 — Mercredi 19/08 — Jalon 1 (Cadrage) + Jalon 2 (Dataset)

**Jalon 1 — Cadrage**
- [x] `docs/cahier_des_charges.md` (problématique, objectifs, périmètre, personas, use cases, KPIs)
- [x] `docs/business_case.md` (première version)
- [x] `docs/rgpd.md`
- [x] Risk register minimal (dans le cahier des charges, pas besoin de fichier Excel séparé en solo)
- [x] Critère de validation : je peux répondre en une phrase à "quel problème, pour qui, avec quelles données, quelle décision, quel impact ?"

**Jalon 2 — Dataset**
- [x] `docs/data_sources.md` déjà prêt (voir audit fourni), à relire et compléter si besoin
- [x] `docs/data_dictionary.md` : une entrée par variable (nom, type, source, signification, transformation, usage)
- [x] `scripts/data_generator.py` opérationnel, seed=42, génère cost_price/stock/promotion/discount
- [x] Échantillon nettoyé exporté dans `data/sample/`
- [x] `docs/data_quality.md` : règles minimales appliquées et testées (9 tests Pytest, dont 3 d'intégration sur l'échantillon réel)

## J2 — Jeudi 20/08 — Jalon 3 (Data Lake R2) + Jalon 4 (Data Warehouse)

**Jalon 3 — Data Lake R2**
- [x] Bucket R2 créé, structure `raw/ processed/` (`features/` réservé aux Jalons 5-7)
- [x] `src/ingestion/` : scripts d'upload Parquet vers R2 (boto3, endpoint S3-compatible)
- [x] Vérification : fichiers uploadés, listés, lus et analysés depuis R2 (via DuckDB) — `make verify-r2`

**Jalon 4 — Data Warehouse**
- [x] DDL SQL (`dim_customer`, `dim_product`, `dim_date`, `dim_promotion`, `fact_sales`, `fact_inventory`, `fact_web_events`) — `data/schemas/ddl.sql`
- [x] ETL processed → PostgreSQL — `make warehouse`
- [x] Vérification : CA, marge, commandes, panier moyen, stock calculables en SQL (36 975 commandes, CA 16 973 707,88, marge 3 499 564,12, panier moyen 459,06 — sous hypothèses des variables synthétiques cost_price/stock/promotion)

## J3 — Vendredi 21/08 — Jalon 5 (Forecasting) + Jalon 6 (Pricing) + Jalon 7 (Recommendation)

Journée la plus chargée : les trois moteurs ML. Travailler dans l'ordre, ne pas paralléliser en solo.

**Jalon 5 — Forecasting**
- [x] Baseline Moving Average
- [x] Comparaison Prophet / LightGBM (Prophet vs baseline sur l'agrégé ; LightGBM global par produit pour l'API — granularités différentes, voir `docs/forecasting.md`)
- [x] Split temporel strict (jamais de random split) — 30 derniers jours en test, testé (`tests/test_forecasting.py`)
- [x] Métriques MAE / RMSE / MAPE (MAPE explose sur ventes proches de 0 comme anticipé — MAE/RMSE retenus comme référence, voir `docs/forecasting.md`)
- [x] Log MLflow (expérience `forecasting`, 3 runs)

**Jalon 6 — Pricing**
- [x] Estimation élasticité à partir de l'historique prix/demande (1057/4631 produits éligibles, régression log-log ; fallback assumé -1,5 documenté pour le reste, cf. `docs/pricing.md`)
- [x] Simulation de prix (grille de 13 points, -30 % à +30 %)
- [x] Sélection du prix qui maximise la marge estimée
- [x] Formulation prudente dans la doc — `docs/pricing.md` (R² médian 0,12 explicitement signalé, uplift jamais présenté comme un gain réel)

**Jalon 7 — Recommendation**
- [x] Baseline Most Popular
- [x] Content-based (catégorie RetailRocket `item_properties`, seul attribut produit disponible côté comportemental — voir `docs/recommendation.md`)
- [x] Collaborative filtering (view/add_to_cart/purchase — TruncatedSVD + FAISS)
- [x] Hybrid (Reciprocal Rank Fusion content-based + collaborative)
- [x] Split temporel train/test sur les interactions (coupure globale, testé)
- [x] Métriques Precision@K / Recall@K / MAP@K (les 3 approches battent la baseline ; espace d'identifiants RetailRocket, pas UCI — voir `docs/recommendation.md` et `docs/api.md`)

## J4 — Samedi 22/08 — Jalon 8 (API) + Jalon 9 (Dashboard) + Jalon 10 (Intégration)

**Jalon 8 — API FastAPI**
- [x] `GET /health`, `GET /forecast/{product_id}`, `GET /pricing/{product_id}`, `GET /recommendations/{customer_id}`, `POST /pricing/simulate` — testés en direct (curl) et via Pytest (`tests/test_api.py`, 9 tests)
- [x] Swagger/OpenAPI généré automatiquement (`/docs`, `/openapi.json` vérifiés HTTP 200)
- [x] Dockerfile API — `requirements-api.txt` allégé (pas de pyspark/prophet/dash inutiles), build + run vérifiés de bout en bout via `docker compose up api` (réseau, Postgres, volume `models/`)

**Jalon 9 — Dashboard Dash**
- [x] Page Executive (KPIs globaux) — `GET /kpis/summary` ajouté à l'API pour l'alimenter
- [x] Page Forecast, Page Pricing, Page Recommendation, Page Inventory
- [x] Connexion à l'API (pas de logique métier dupliquée dans le dashboard) — vérifié de bout en bout via `docker compose up dashboard` (réseau dashboard -> api -> Postgres), palette dataviz appliquée (skill dataviz)

**Jalon 10 — Intégration**
- [x] Chaîne complète R2 → PostgreSQL → ML → MLflow → FastAPI → Dash fonctionnelle de bout en bout — vérifié après `docker compose down && docker compose up -d --build` complet (redémarrage à froid, volumes Postgres persistés)
- [x] Docker Compose complet (API + Dashboard + Postgres + MLflow) — les 4 services démarrent et communiquent correctement sur le réseau interne
- [x] Tests pytest (data quality, API, pricing, recommendation, transformations, streaming) — 68 tests (64 + 4 streaming ajoutés lors du Jalon Kafka), dont 35 tournent sans données locales (simulé en écartant temporairement data/raw_local, models/, data/sample/ — 35 passed, 29 skipped proprement, 0 échec)
- [x] GitHub Actions CI (tests + build) — bug corrigé : le workflow ne se déclenchait que sur `main`, jamais utilisé (le repo n'a que `master`) ; job `build` ajouté (matrice api/dashboard, Dockerfiles allégés Jalon 8/9)
- [x] Kafka (streaming simulé) — profil Docker Compose séparé (`streaming`), producteur/consommateur Python (`src/streaming/`), vérifié de bout en bout le 23/08 (20 événements produits → consommés → insérés dans `fact_web_events` sans perte ni doublon). Voir `docs/architecture.md`, section Streaming simulé
- [ ] Airflow **seulement si le temps le permet** — ne jamais le prioriser au détriment des 3 modèles ou du dashboard (règle explicite du brief, section 29.8) — volontairement non traité faute de temps

## J5 — Dimanche 23/08 — Jalon 11 (Documentation) + Jalon 12 (Soutenance) — DEADLINE

- [ ] README complet (installation, lancement, architecture)
- [ ] Documentation technique à jour (architecture, data dictionary, sources, API, modèles, limitations)
- [ ] Rapport final structuré selon les 12 chapitres du brief (section 47)
- [ ] Slides de soutenance (15 min, plan de la section 51 du brief)
- [ ] Script de démo répété au moins une fois (scénario section 50 : dashboard → stock → forecast → pricing → recommendation → décision)
- [ ] Checklist finale (section 52 du brief) passée en revue
- [ ] Repository GitHub propre, `.env` absent de l'historique, README à jour
- [ ] Marge de sécurité : viser une version livrable en fin de matinée, garder l'après-midi pour les répétitions et corrections

## Rappel — en cas de retard

Respecter strictement l'ordre de sacrifice du brief (section 53) :

1. Fondations (dataset, data lake, data warehouse) — jamais sacrifiées
2. Intelligence (forecasting, pricing, recommendation) — jamais sacrifiées
3. Produit (API, dashboard) — jamais sacrifié
4. Industrialisation (Docker, MLflow, tests, CI/CD) — à réduire si besoin, pas à supprimer
5. Infrastructure avancée (Kafka, Airflow) — premier poste sacrifiable
6. Bonus (A/B testing, CLTV, churn, XAI) — à ignorer complètement si le temps manque
