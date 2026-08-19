# Plateforme Data-Driven Pricing & Recommandation — E-commerce local

Projet final Master 2 Big Data (ISM / Gestion de Projet Data & EBusiness). Plateforme décisionnelle de bout en bout : forecasting de la demande, dynamic pricing, système de recommandation, exposés via une API FastAPI et un dashboard Dash.

## Voir le projet fonctionner en 2 commandes (correction / démo)

Aucun compte externe requis (ni Cloudflare R2, ni Kaggle) : un instantané de démonstration (base PostgreSQL déjà peuplée + modèles déjà entraînés, dossier `demo/`) est inclus dans le repo pour que le dashboard soit consultable immédiatement.

**Prérequis : uniquement [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et lancé.**

```bash
git clone https://github.com/Fadel076m/ecommerce-pricing-recommendation.git
cd ecommerce-pricing-recommendation
make demo
```

(Pas de `make` sous la main, par exemple sous Windows sans Git Bash ? Lancer directement `bash scripts/restore_demo.sh`, ou ouvrir ce fichier et exécuter ses commandes une par une.)

Ce script :
1. copie `.env.example` vers `.env` si absent (valeurs de démo locales, aucun identifiant à saisir) ;
2. démarre PostgreSQL et MLflow ;
3. restaure la base de démo (`demo/warehouse_dump.dump`) et les modèles pré-entraînés (`demo/models/`) ;
4. construit et démarre l'API et le dashboard.

Au bout de quelques minutes (premier build des images Docker) :

| Service | URL | Contenu |
|---|---|---|
| **Dashboard** | http://localhost:8050 | Vue d'ensemble, prévision, tarification, recommandations, stock |
| **API (Swagger)** | http://localhost:8000/docs | Documentation interactive de tous les endpoints |
| **MLflow** | http://localhost:5000 | Expériences et métriques des 3 moteurs (forecasting/pricing/recommendation) |

Pour tout arrêter : `docker compose down` (les données restent dans les volumes Docker, `make demo` peut être relancé à tout moment).

## Développement complet (reproduction depuis les données brutes)

Pour retravailler le pipeline depuis les sources publiques (UCI Online Retail II, RetailRocket, Dunnhumby Complete Journey) plutôt que l'instantané de démo — nécessite de télécharger ces trois sources (voir `docs/data_sources.md`) et, pour uploader vers le Data Lake, des identifiants Cloudflare R2 :

```bash
cp .env.example .env        # puis remplir les identifiants R2 si besoin de `make ingest`
make setup                  # crée le venv (uv si présent, sinon venv/pip) et installe les dépendances
make docker-up               # lance Postgres + MLflow
make warehouse                # DDL + ETL vers PostgreSQL (nécessite data/raw_local/, non versionné)
make forecast pricing recommend   # entraîne et évalue les 3 moteurs, logge dans MLflow
make api                     # API FastAPI sur :8000 (Swagger sur /docs)
make dashboard                # Dashboard Dash sur :8050
make test                     # suite de tests Pytest
make memory                   # affiche les derniers commits + dernière entrée du journal de session
```

## Documentation

Toute la documentation projet est dans `docs/` :

- `docs/roadmap.md` — jalons datés, checklist, deadline
- `docs/data_sources.md`, `docs/data_dictionary.md`, `docs/data_quality.md` — données, modèle, contrôles
- `docs/architecture.md`, `docs/api.md` — architecture technique
- `docs/forecasting.md`, `docs/pricing.md`, `docs/recommendation.md` — méthodologie et résultats des 3 moteurs ML
- `docs/rgpd.md`, `docs/business_case.md` — cadrage business et conformité
- `docs/cahier_des_charges.md` — cadrage initial
