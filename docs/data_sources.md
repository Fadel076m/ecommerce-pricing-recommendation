# Sources de données — audit réel (18/08/2026)

Ce document remplace la section "stratégie des datasets" du brief par un état des lieux basé sur les fichiers réellement présents dans `Projet Ecommerce/data` sur la machine locale. Il fait foi pour l'ingestion (Jalon 2 et 3).

## 1. UCI Online Retail II — source principale (transactions / clients / produits / prix)

- Fichiers : `online_retail_II.xlsx` (2 feuilles : `Year 2009-2010`, `Year 2010-2011`)
- Redondant à ignorer : `online+retail+ii.zip` (contenu déjà extrait dans le xlsx)
- Colonnes confirmées : InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country
- Statut : complet, conforme au brief. Poids modéré (~46 Mo), chargeable directement avec pandas ou DuckDB.
- Usage : `dim_customer`, `dim_product`, `fact_sales`, base du forecasting et du pricing.

## 2. RetailRocket — source comportementale (recommandation)

- Fichiers : `events.csv` (94 Mo), `item_properties_part1.csv` (484 Mo), `item_properties_part2.csv` (409 Mo), `category_tree.csv` (14 Ko)
- Redondant à ignorer : `archive (1).zip` (304 Mo, contenu déjà extrait)
- Colonnes confirmées : `events.csv` → timestamp, visitorid, event (view/addtocart/transaction), itemid, transactionid ; `item_properties_*` → timestamp, itemid, property, value
- Statut : complet, conforme au brief. **Volumineux (~900 Mo pour les deux parts d'item_properties)** — ne jamais charger avec `pandas.read_csv` brut. Utiliser DuckDB (lecture streaming/colonne) ou PySpark, et ne garder que les `itemid` présents dans `events.csv` avant de joindre les propriétés.
- Usage : `fact_web_events`, features de recommandation (content-based via propriétés, collaborative via events).

## 3. Dunnhumby Complete Journey — source complémentaire (stock / promos / coupons)

- Fichiers : `transaction_data.csv` (142 Mo), `product.csv` (6,4 Mo), `hh_demographic.csv` (43 Ko), `campaign_desc.csv`, `campaign_table.csv`, `coupon.csv` (2,8 Mo), `coupon_redempt.csv` (54 Ko), `causal_data.csv` (**696 Mo**)
- Redondant à ignorer : `archive (2).zip` (45 Mo)
- **À ne pas utiliser** : `dunnhumby - Breakfast at the Frat.xlsx/pdf/zip` — c'est un dataset Dunnhumby différent (étude marketing dédiée), hors périmètre.
- Statut : complet, conforme au brief. `causal_data.csv` est le fichier le plus lourd du projet (display/mailer par produit-magasin-semaine) et n'est utile que pour l'analyse promotionnelle avancée. **Recommandation : ne pas l'ingérer en Jalon 2-3 ; le garder en réserve pour un enrichissement pricing/promotion si le temps le permet.**
- Usage : `dim_promotion`, `fact_inventory` (proxy stock via ventes), variables synthétiques de coût/stock à générer en s'appuyant sur `product.csv` et `hh_demographic.csv`.

## 4. M5 (Walmart) — référence forecasting, optionnelle

- **Non téléchargée.** Le brief la présente comme un benchmark facultatif ("préférable de l'utiliser comme référence séparée"). Décision : **volontairement écartée** pour tenir le délai de 6 jours. Aucune action requise, à mentionner explicitement dans `docs/data_quality.md` comme un choix assumé et non un oubli.

## 5. Olist Brazilian E-Commerce — hors périmètre du brief

- Fichiers présents : `olist_customers`, `olist_geolocation`, `olist_order_items`, `olist_order_payments`, `olist_order_reviews`, `olist_orders`, `olist_products`, `olist_sellers`, `product_category_name_translation` (~127 Mo au total)
- Ce dataset n'apparaît dans aucun des deux énoncés (ni ISM, ni Gestion de Projet). Le brief interdit explicitement (section 13) de mélanger des sources hétérogènes dans une même table sans les faire passer par un modèle de données cohérent.
- **Décision : ne pas l'utiliser pour le MVP.** Il peut servir de source bonus ultérieure (ex. données produits réalistes avec avis clients) si le temps le permet après le Jalon 9, mais ne doit jamais être fusionné directement avec UCI/RetailRocket/Dunnhumby.

## 6. Volumétrie totale et conséquence sur R2

Le dossier `data/` pèse environ **2,6 Go** en l'état (zips redondants inclus). Cloudflare R2 free tier a des quotas de stockage et d'opérations (cf. section 6.2 du brief ISM). Conséquence pratique :

1. Ne jamais uploader les fichiers bruts tels quels sur R2.
2. Nettoyer/filtrer/échantillonner en local avec DuckDB avant tout upload (ne garder que les colonnes et lignes utiles).
3. Les couches `raw/` sur R2 doivent contenir un sous-ensemble documenté, pas l'intégralité des sources — la couche `processed/` (Parquet) sera de toute façon beaucoup plus légère.
4. Supprimer localement les zips redondants (`archive (1).zip`, `archive (2).zip`, `online+retail+ii.zip`) une fois les CSV/xlsx confirmés lisibles, pour libérer de l'espace disque de travail.

## Tableau récapitulatif

| Source | Fichiers clés | Poids | Statut | Usage principal |
|---|---|---|---|---|
| UCI Online Retail II | online_retail_II.xlsx | ~46 Mo | OK | transactions, clients, produits, prix |
| RetailRocket | events.csv, item_properties_part1/2.csv, category_tree.csv | ~900 Mo | OK, volumineux | comportement, recommandation |
| Dunnhumby Complete Journey | transaction_data.csv, product.csv, hh_demographic.csv, campaign_*, coupon_*, causal_data.csv | ~850 Mo | OK, causal_data à différer | promotions, stock synthétique, coupons |
| M5 | — | — | non téléchargé, écarté volontairement | — |
| Olist | olist_*.csv | ~127 Mo | hors périmètre, non utilisé pour le MVP | bonus optionnel |
