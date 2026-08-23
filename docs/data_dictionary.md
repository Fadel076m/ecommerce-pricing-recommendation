# Data Dictionary

> Une ligne par variable, jamais de variable non documentée. Modèle en étoile imposé par le brief ISM (section 11) : `dim_customer`, `dim_product`, `dim_date`, `dim_promotion`, `fact_sales`, `fact_inventory`, `fact_web_events`. Statuts utilisés dans la colonne "Source" :
>
> - **Observé** : valeur directement présente dans une source publique.
> - **Dérivé** : calculée/transformée à partir d'une ou plusieurs colonnes observées (règle explicite, pas de hasard).
> - **Synthétique (seed=42)** : générée par `scripts/data_generator.py`, aucune contrepartie réelle dans les sources publiques — jamais à présenter comme une donnée observée.
>
> Le brief (section 11.6) nomme cette table `fact_promotions` ; la roadmap et l'arborescence du repo la nomment `dim_promotion`. On retient `dim_promotion` — note conservée ici pour éviter la confusion en Jalon 4.

## dim_customer

| Colonne | Type | Source | Signification | Transformation | Usage |
|---|---|---|---|---|---|
| customer_id | string | Observé — UCI Online Retail II (`CustomerID`) | identifiant client anonymisé | cast en string, préfixe `CUST_` | clé de jointure, RFM, recommendation |
| age | int | Synthétique (seed=42) | âge du client | tirage aléatoire borné (18-75), non fourni par UCI | segmentation, persona |
| gender | string | Synthétique (seed=42) | genre du client | tirage aléatoire (M/F/Autre), non fourni par UCI | segmentation |
| city | string | Observé — UCI Online Retail II (`Country`, agrégé) | localisation client | UCI ne fournit que le pays, pas la ville : `city` reste au niveau pays jusqu'à nouvel ordre (à documenter comme approximation) | segmentation géographique |
| segment | string | Dérivé — calculé sur `fact_sales` | segment RFM (Récence/Fréquence/Montant) | calculé en Jalon 4 (ETL) à partir de l'historique de commandes, pas disponible avant le Data Warehouse | ciblage, recommendation |
| registration_date | date | Dérivé — proxy = date de première commande observée dans `fact_sales` | date d'entrée du client | UCI ne fournit pas de date d'inscription réelle ; proxy documenté comme approximation, pas une vraie date d'inscription | ancienneté, churn (bonus) |

## dim_product

| Colonne | Type | Source | Signification | Transformation | Usage |
|---|---|---|---|---|---|
| product_id | string | Observé — UCI Online Retail II (`StockCode`) | identifiant produit | renommage | clé de jointure |
| product_name | string | Observé — UCI Online Retail II (`Description`) | libellé produit | nettoyage texte (trim, casse) | affichage, content-based recommendation |
| category | string | Dérivé — règles de classification sur `product_name` | catégorie produit | UCI ne fournit pas de catégorie ; classification par mots-clés à définir en Jalon 3, jamais présentée comme une catégorie officielle du vendeur | filtrage, pricing par catégorie |
| subcategory | string | Dérivé — règles de classification sur `product_name` | sous-catégorie produit | même limite que `category` | filtrage |
| brand | string | Dérivé — règles de classification sur `product_name`, quand identifiable | marque produit | absent d'UCI ; laissé `unknown` quand non identifiable plutôt qu'inventé | filtrage, content-based recommendation |
| cost_price | float | Synthétique (seed=42) | coût d'achat unitaire | `generate_cost_price()` : `base_price × (1 - marge aléatoire 15-45%)` | calcul de marge, pricing |
| base_price | float | Observé — UCI Online Retail II (`UnitPrice`, moyenne historique par produit) | prix de référence hors promotion | agrégation (médiane) des `UnitPrice` observés pour le `StockCode` | pricing (point de départ de la simulation) |
| current_price | float | Observé — UCI Online Retail II (`UnitPrice`, dernière valeur observée) | prix affiché actuellement | dernière transaction connue pour le produit | pricing, dashboard |

## dim_date

| Colonne | Type | Source | Signification | Transformation | Usage |
|---|---|---|---|---|---|
| date_id | int | Dérivé | clé technique (format `YYYYMMDD`) | généré pour chaque date calendaire de la période couverte | clé de jointure |
| date | date | Dérivé | date calendaire | — | affichage, filtre temporel |
| year / month / day | int | Dérivé | composantes calendaires | extraites de `date` | agrégations temporelles |
| weekday | int | Dérivé | jour de la semaine (0-6) | extrait de `date` | saisonnalité (forecasting) |
| is_weekend | bool | Dérivé | week-end ou non | `weekday >= 5` | saisonnalité |

## dim_promotion

| Colonne | Type | Source | Signification | Transformation | Usage |
|---|---|---|---|---|---|
| promotion_id | string | Synthétique (seed=42) | identifiant promotion | généré | clé de jointure |
| product_id | string | Observé (référence à `dim_product`) | produit concerné | — | jointure |
| start_date / end_date | date | Synthétique (seed=42) | période de la promotion | `generate_promotion()` : tirage de fenêtres promotionnelles | pricing, effet promo sur la demande |
| discount_percentage | float | Synthétique (seed=42) | taux de remise | `generate_promotion()` : tirage borné (5-30%), probabilité 15% par produit/période | pricing, forecasting (variable exogène) |

Complémentaire possible (non prioritaire, Jalon 6+) : `Dunnhumby` fournit de vraies données de campagnes/coupons (`campaign_desc.csv`, `coupon.csv`) qui pourraient remplacer une partie de cette table par des promotions observées plutôt que synthétiques — non fait au MVP faute de temps, à documenter si repris.

## fact_sales

| Colonne | Type | Source | Signification | Transformation | Usage |
|---|---|---|---|---|---|
| order_id | string | Observé — UCI Online Retail II (`InvoiceNo`) | identifiant commande | renommage | clé, agrégation panier |
| customer_id | string | Observé — UCI Online Retail II (`CustomerID`) | référence client | — | jointure `dim_customer` |
| product_id | string | Observé — UCI Online Retail II (`StockCode`) | référence produit | — | jointure `dim_product` |
| date_id | int | Dérivé — depuis `InvoiceDate` | référence date | cast `InvoiceDate` → `date_id` | jointure `dim_date` |
| quantity | int | Observé — UCI Online Retail II (`Quantity`) | quantité vendue | lignes `Quantity <= 0` exclues (retours/annulations, cf. `docs/data_quality.md`) | CA, forecasting |
| unit_price | float | Observé — UCI Online Retail II (`UnitPrice`) | prix unitaire facturé | — | CA, pricing |
| discount | float | Synthétique (seed=42) | remise appliquée sur la ligne | reprise de `dim_promotion` si le produit est en promotion à la date, 0 sinon | marge, pricing |
| revenue | float | Dérivé | chiffre d'affaires de la ligne | `quantity × unit_price × (1 - discount)` | KPI Commercial |
| cost | float | Dérivé | coût de la ligne | `quantity × cost_price` (jointure `dim_product`) | marge |
| margin | float | Dérivé | marge de la ligne | `revenue - cost` | KPI Marge, pricing |

## fact_inventory

> Simplification MVP assumée : un seul instantané de stock par produit (`date_id` = dernière date observée dans `fact_sales`), pas une série temporelle quotidienne complète — suffisant pour le calcul de risque de rupture/surstock du dashboard (use case 2), documenté explicitement pour ne pas être confondu avec un historique de stock réel.

| Colonne | Type | Source | Signification | Transformation | Usage |
|---|---|---|---|---|---|
| product_id | string | Observé (référence à `dim_product`) | produit concerné | — | jointure |
| date_id | int | Dérivé | date de l'instantané (dernière date observée dans `fact_sales`) | — | jointure `dim_date` |
| opening_stock | int | Synthétique (seed=42) | stock en début de période | `generate_stock_movement()`, calibré sur `avg_daily_sales` observé | KPI Stock, rupture/surstock |
| stock_in | int | Synthétique (seed=42) | réapprovisionnement de la période | `generate_stock_movement()` | KPI Stock |
| quantity_sold | int | Observé — agrégation de `fact_sales.quantity` par produit/date | quantité vendue sur la période | somme des ventes observées | cohérence stock, forecasting |
| closing_stock | int | Dérivé | stock en fin de période | `opening_stock + stock_in - quantity_sold` (règle de cohérence vérifiée en test, cf. `docs/data_quality.md`) | KPI Stock, rupture/surstock |

## fact_web_events

Schéma tel qu'implémenté (`src/transformation/web_events.py`, `data/schemas/ddl.sql`) — sans clé étrangère vers `dim_customer`/`dim_product` (voir note ci-dessous).

| Colonne | Type | Source | Signification | Transformation | Usage |
|---|---|---|---|---|---|
| event_id | string | Dérivé | identifiant événement | généré positionnellement (`"EVT_" + index`) au chargement batch — `transactionid` RetailRocket n'est **pas** utilisable tel quel (un même `transactionid` couvre plusieurs lignes/items d'un même panier) ; le streaming simulé (Kafka, Jalon 10) utilise un préfixe distinct `STREAM_EVT_` pour ne jamais entrer en collision (cf. `docs/architecture.md`) | clé technique (PK) |
| visitor_id | string | Observé — RetailRocket (`visitorid`) | référence visiteur | renommage, anonymisé par l'éditeur de la source (cf. `docs/rgpd.md`) | filtrage/agrégation — **note : `visitorid` RetailRocket et `customer_id` UCI sont des espaces d'identifiants distincts, jamais fusionnés directement, pas de clé étrangère commune** |
| item_id | string | Observé — RetailRocket (`itemid`) | référence produit consulté | renommage | filtrage/agrégation — **même note : `itemid` RetailRocket ≠ `product_id` UCI (`StockCode`), espaces distincts** |
| session_id | string | Dérivé — reconstruit à partir de `visitor_id` + fenêtre temporelle (RetailRocket ne fournit pas de `session_id` explicite) | session de navigation | découpage par inactivité : plus de 30 minutes sans événement pour un même visiteur = nouvelle session (`SESSION_GAP_MINUTES`) | recommendation collaborative |
| event_type | string | Observé — RetailRocket (`event` : view / addtocart / transaction) | type d'événement | renommage vers la nomenclature du brief (`view`, `add_to_cart`, `purchase`) | pondération recommendation (`view`=1, `add_to_cart`=3, `purchase`=5) |
| event_time | datetime | Observé — RetailRocket (`timestamp`, epoch ms) | horodatage de l'événement | conversion epoch ms → datetime | split temporel strict (recommendation, cf. `docs/recommendation.md`) |

## Note sur les espaces d'identifiants

Rappel explicite : le `customer_id`/`product_id` de `fact_sales` (UCI) et le `visitor_id`/`item_id` de `fact_web_events` (RetailRocket) ne référencent **pas** les mêmes individus/produits réels — ce sont deux sources indépendantes avec des identifiants propres. Elles ne sont jamais fusionnées par identifiant direct ; `fact_web_events` n'a aucune clé étrangère vers `dim_customer`/`dim_product` (cf. `data/schemas/ddl.sql`), et les usages cross-source (ex. recommendation hybride) passent par des features agrégées, jamais par une jointure `customer_id = visitor_id`.

## Note sur l'ingestion batch + streaming de fact_web_events

`fact_web_events` est alimentée par deux chemins qui écrivent dans la même table (Jalon 10) :
- **Batch** (historique complet) : `src/transformation/web_events.py`, `event_id` préfixé `EVT_`.
- **Streaming simulé** (Kafka, démonstration) : `src/streaming/producer.py` rejoue un échantillon versionné (`data/sample/fact_web_events_sample.parquet`) sur un topic Kafka, `src/streaming/consumer.py` insère chaque événement au fil de l'eau, `event_id` préfixé `STREAM_EVT_` — préfixe distinct pour ne jamais entrer en collision avec la clé primaire du batch. Détail dans `docs/architecture.md`.
