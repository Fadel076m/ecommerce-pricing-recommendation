# Data Quality

## Contrôles minimums (repris du brief, à implémenter en tests Pytest)

**Clients**
- customer_id IS NOT NULL, UNIQUE

**Produits**
- product_id IS NOT NULL
- price >= 0, cost_price >= 0

**Transactions**
- quantity > 0
- unit_price >= 0
- revenue >= 0

**Stock**
- opening_stock >= 0, stock_in >= 0, closing_stock >= 0
- closing_stock = opening_stock + stock_in - quantity_sold

**Business rules**
- revenue = quantity × unit_price × (1 - discount)
- margin = revenue - cost

## Sources écartées ou différées (transparence)

- M5 : non téléchargé, choix assumé (source de référence optionnelle)
- Olist : téléchargé mais hors périmètre, non utilisé dans le MVP
- Dunnhumby `causal_data.csv` : ingestion différée (volumétrie ~696 Mo), à intégrer seulement si le temps le permet après le Jalon 6

## Transparence sur les données synthétiques

Le dataset final est un jeu de données composite destiné à un prototype académique. Les données transactionnelles et comportementales proviennent de sources publiques documentées. Les variables non disponibles dans les sources publiques (coût, stock, promotion) sont générées ou dérivées synthétiquement afin de compléter le scénario e-commerce. Les résultats business issus de ces variables sont donc des simulations, pas des performances observées sur une entreprise réelle.
