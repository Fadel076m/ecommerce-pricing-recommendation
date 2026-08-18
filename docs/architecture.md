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

Schéma détaillé à documenter dans `docs/data_dictionary.md` au fur et à mesure du Jalon 4.
