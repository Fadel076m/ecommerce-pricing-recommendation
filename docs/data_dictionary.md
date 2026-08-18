# Data Dictionary

> À compléter au fil des jalons 2 à 4. Une ligne par variable, jamais de variable non documentée.

| Table | Colonne | Type | Source | Signification | Transformation | Usage |
|---|---|---|---|---|---|---|
| fact_sales | order_id | string | UCI Online Retail II (InvoiceNo) | identifiant commande | renommage | clé de jointure |
| ... | ... | ... | ... | ... | ... | ... |

Marquer explicitement dans la colonne "Source" les variables **synthétiques** (générées par `scripts/data_generator.py`, seed=42) pour ne jamais les confondre avec des données observées.
