# Architecture technique

## Vue d'ensemble

```
SOURCES DE DONNÉES (UCI Online Retail II, RetailRocket, Dunnhumby)
        │
        ↓
PIPELINE INGESTION (Python / PySpark)
        │
        ↓
CLOUDFLARE R2 — DATA LAKE (Parquet : raw / processed / features)
        │
   ┌────┴────┐
   ↓         ↓
DuckDB    PySpark
   └────┬────┘
        ↓
POSTGRESQL — DATA WAREHOUSE (modèle en étoile)
        │
   ┌────┼────┐
   ↓    ↓    ↓
Forecasting Pricing Recommendation
   └────┼────┘
        ↓
     MLflow
        ↓
     FastAPI
        ↓
       Dash
        ↓
DASHBOARD DÉCISIONNEL
```

Détail complet dans le brief ISM (section 5 et 54).

## Modèle en étoile (Data Warehouse)

- `dim_customer`, `dim_product`, `dim_date`, `dim_promotion`
- `fact_sales`, `fact_inventory`, `fact_web_events`

Schéma détaillé dans `docs/data_dictionary.md`, DDL dans `data/schemas/ddl.sql`.

## Pipeline opérationnel (Jalon 3/4)

- `make ingest` (`src/ingestion/upload_to_r2.py`) : construit le modèle en étoile (`src/transformation/star_schema.py`) + `fact_web_events` (`src/transformation/web_events.py`) à partir des sources dans `data/raw_local/` (non versionné), et uploade `raw/` + `processed/` vers R2 en Parquet.
- `make verify-r2` (`src/ingestion/verify_r2.py`) : liste les objets R2 (boto3) et les relit/analyse via DuckDB (secret S3 générique, `URL_STYLE 'path'` — le type `r2` natif de DuckDB a échoué en 404 sur ce bucket).
- `make warehouse` (`src/transformation/load_to_postgres.py`) : applique `data/schemas/ddl.sql` puis charge les 7 tables dans PostgreSQL.
- Validé de bout en bout le 19/08 : 779 495 lignes `fact_sales`, 2 756 101 `fact_web_events`, CA/marge/panier moyen/risque de rupture calculables en SQL — cohérents entre R2 et PostgreSQL.

## Streaming simulé (Kafka, Jalon 10)

Le brief demande une ingestion batch **et** un streaming simulé. Le batch (ci-dessus) charge l'historique complet ; Kafka démontre la coexistence d'un flux d'événements arrivant en continu sur la **même table cible** (`fact_web_events`), sans dupliquer la logique métier.

```
data/sample/fact_web_events_sample.parquet (échantillon versionné, 2000 événements RetailRocket)
        │
        ↓
   PRODUCTEUR (src/streaming/producer.py) — un message JSON toutes les ~0,2s
        │
        ↓
   Kafka (topic ecommerce.web_events, 1 broker, mode KRaft)
        │
        ↓
   CONSOMMATEUR (src/streaming/consumer.py) — INSERT ... ON CONFLICT DO NOTHING
        │
        ↓
   PostgreSQL — fact_web_events (même table que le chargement batch)
```

- **Optionnel et isolé** : Kafka vit derrière le profil Docker Compose `streaming` (`docker-compose.yml`), jamais démarré par `docker compose up` par défaut ni par `make demo` — aucun risque pour le chemin de démonstration principal.
- **Échantillon dédié, pas les données brutes** : `data/sample/fact_web_events_sample.parquet` (2000 lignes, généré par `scripts/data_generator.py::export_web_events_sample`, seed=42) est versionné pour que la démo streaming fonctionne sans `data/raw_local/events.csv` (94 Mo, non versionné).
- **Pas de collision avec le batch** : les événements rejoués reçoivent un `event_id` préfixé `STREAM_EVT_` (`src/streaming/events.py`), distinct du `EVT_` généré par le chargement batch (`src/transformation/web_events.py`).
- **Idempotent** : `ON CONFLICT (event_id) DO NOTHING` — rejouer la démo plusieurs fois ne duplique rien.
- **Auto-terminant pour la démo** : le consommateur s'arrête après 15 secondes sans nouveau message (`consumer_timeout_ms`) — pas un service qui tourne indéfiniment comme le ferait un vrai consommateur de production.
- Vérifié de bout en bout le 23/08 : 20 événements produits → consommés → insérés dans `fact_web_events` sans perte ni doublon.

Lancer la démo : voir README.md, section Streaming simulé.
