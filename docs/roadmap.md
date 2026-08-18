# Roadmap — Jalons datés (deadline dimanche 23/08/2026)

Mode solo + agents IA (Claude Code / Codex). Les 12 jalons du brief ISM sont compressés sur 6 jours, dans l'ordre de priorité imposé par la section 53 du brief ("Priorités en cas de problème") : Fondations → Intelligence → Produit → Industrialisation → Infrastructure avancée (sacrifiable) → Bonus (sacrifiable).

Chaque jalon doit se terminer par un commit git dédié et une mise à jour de la checklist ci-dessous.

## J0 — Mardi 18/08 (reste de journée)

**Objectif** : setup technique prêt à coder.

- [ ] Repo initialisé, structure créée, `AGENTS.md`/`CLAUDE.md` en place
- [ ] `.env` rempli localement (jamais commité)
- [ ] `docker compose up -d` fonctionnel (Postgres + MLflow)
- [ ] Environnement Python créé, `requirements.txt` installé
- [ ] Démarrage Jalon 1 (cadrage) : problématique, objectifs, périmètre MVP rédigés

## J1 — Mercredi 19/08 — Jalon 1 (Cadrage) + Jalon 2 (Dataset)

**Jalon 1 — Cadrage**
- [ ] `docs/cahier_des_charges.md` (problématique, objectifs, périmètre, personas, use cases, KPIs)
- [ ] `docs/business_case.md` (première version)
- [ ] `docs/rgpd.md`
- [ ] Risk register minimal (dans le cahier des charges, pas besoin de fichier Excel séparé en solo)
- [ ] Critère de validation : je peux répondre en une phrase à "quel problème, pour qui, avec quelles données, quelle décision, quel impact ?"

**Jalon 2 — Dataset**
- [ ] `docs/data_sources.md` déjà prêt (voir audit fourni), à relire et compléter si besoin
- [ ] `docs/data_dictionary.md` : une entrée par variable (nom, type, source, signification, transformation, usage)
- [ ] `scripts/data_generator.py` opérationnel, seed=42, génère cost_price/stock/promotion/discount
- [ ] Échantillon nettoyé exporté dans `data/sample/`
- [ ] `docs/data_quality.md` : règles minimales appliquées et testées

## J2 — Jeudi 20/08 — Jalon 3 (Data Lake R2) + Jalon 4 (Data Warehouse)

**Jalon 3 — Data Lake R2**
- [ ] Bucket R2 créé, structure `raw/ processed/ features/`
- [ ] `src/ingestion/` : scripts d'upload Parquet vers R2 (boto3, endpoint S3-compatible)
- [ ] Vérification : fichiers uploadés, listés, lus et analysés depuis R2 (via DuckDB)

**Jalon 4 — Data Warehouse**
- [ ] DDL SQL (`dim_customer`, `dim_product`, `dim_date`, `dim_promotion`, `fact_sales`, `fact_inventory`, `fact_web_events`)
- [ ] ETL processed → PostgreSQL
- [ ] Vérification : CA, marge, commandes, panier moyen, stock calculables en SQL

## J3 — Vendredi 21/08 — Jalon 5 (Forecasting) + Jalon 6 (Pricing) + Jalon 7 (Recommendation)

Journée la plus chargée : les trois moteurs ML. Travailler dans l'ordre, ne pas paralléliser en solo.

**Jalon 5 — Forecasting**
- [ ] Baseline Moving Average
- [ ] Comparaison Prophet / LightGBM
- [ ] Split temporel strict (jamais de random split)
- [ ] Métriques MAE / RMSE / MAPE (attention MAPE si ventes proches de 0)
- [ ] Log MLflow

**Jalon 6 — Pricing**
- [ ] Estimation élasticité à partir de l'historique prix/demande
- [ ] Simulation de prix (plusieurs points de prix testés)
- [ ] Sélection du prix qui maximise la marge estimée
- [ ] Formulation prudente dans la doc ("sous les hypothèses du modèle...")

**Jalon 7 — Recommendation**
- [ ] Baseline Most Popular
- [ ] Content-based (category/brand/description)
- [ ] Collaborative filtering (view/add_to_cart/purchase)
- [ ] Hybrid (combinaison des scores)
- [ ] Split temporel train/test sur les interactions
- [ ] Métriques Precision@K / Recall@K / MAP@K

## J4 — Samedi 22/08 — Jalon 8 (API) + Jalon 9 (Dashboard) + Jalon 10 (Intégration)

**Jalon 8 — API FastAPI**
- [ ] `GET /health`, `GET /forecast/{product_id}`, `GET /pricing/{product_id}`, `GET /recommendations/{customer_id}`, `POST /pricing/simulate`
- [ ] Swagger/OpenAPI généré automatiquement
- [ ] Dockerfile API

**Jalon 9 — Dashboard Dash**
- [ ] Page Executive (KPIs globaux)
- [ ] Page Forecast, Page Pricing, Page Recommendation, Page Inventory
- [ ] Connexion à l'API (pas de logique métier dupliquée dans le dashboard)

**Jalon 10 — Intégration**
- [ ] Chaîne complète R2 → PostgreSQL → ML → MLflow → FastAPI → Dash fonctionnelle de bout en bout
- [ ] Docker Compose complet (API + Dashboard + Postgres + MLflow)
- [ ] Tests pytest (data quality, API, pricing, recommendation, transformations)
- [ ] GitHub Actions CI (tests + build)
- [ ] Kafka et Airflow **seulement si le temps le permet** — ne jamais les prioriser au détriment des 3 modèles ou du dashboard (règle explicite du brief, section 29.8)

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
