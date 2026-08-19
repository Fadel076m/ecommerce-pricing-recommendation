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

Détail complet dans le brief ISM (section 5 et 54). Stack figée dans `AGENTS.md`.

## Modèle en étoile (Data Warehouse)

- `dim_customer`, `dim_product`, `dim_date`, `dim_promotion`
- `fact_sales`, `fact_inventory`, `fact_web_events`

Schéma détaillé dans `docs/data_dictionary.md`, DDL dans `data/schemas/ddl.sql`.

## Pipeline opérationnel (Jalon 3/4)

- `make ingest` (`src/ingestion/upload_to_r2.py`) : construit le modèle en étoile (`src/transformation/star_schema.py`) + `fact_web_events` (`src/transformation/web_events.py`) à partir des sources dans `data/raw_local/` (non versionné), et uploade `raw/` + `processed/` vers R2 en Parquet.
- `make verify-r2` (`src/ingestion/verify_r2.py`) : liste les objets R2 (boto3) et les relit/analyse via DuckDB (secret S3 générique, `URL_STYLE 'path'` — le type `r2` natif de DuckDB a échoué en 404 sur ce bucket).
- `make warehouse` (`src/transformation/load_to_postgres.py`) : applique `data/schemas/ddl.sql` puis charge les 7 tables dans PostgreSQL.
- Validé de bout en bout le 19/08 : 779 495 lignes `fact_sales`, 2 756 101 `fact_web_events`, CA/marge/panier moyen/risque de rupture calculables en SQL — cohérents entre R2 et PostgreSQL.
