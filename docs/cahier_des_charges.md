# Cahier des charges — Jalon 1

> Jalon 1 (Cadrage), démarré en J0 (18/08) et finalisé le 19/08. Structure imposée par le brief ISM, section "Chapitre 1 — Introduction" et "Chapitre 2 — Cadrage business".

## Problématique

Comment exploiter les données transactionnelles, comportementales, produits, prix, promotions et stocks d'un e-commerce local afin d'améliorer la marge, la disponibilité des produits, la conversion et la fidélisation des clients ?

## Objectifs business

Repris tels quels du brief ISM (section 3.1) :

- Augmenter la marge
- Réduire les ruptures de stock
- Réduire les surstocks
- Améliorer la conversion
- Augmenter le panier moyen
- Favoriser le cross-sell
- Favoriser l'up-sell
- Améliorer la personnalisation
- Aider les responsables à prendre des décisions basées sur les données

## Objectifs techniques

Repris du brief ISM (section 3.2), le projet doit démontrer :

- une architecture Data Lake (R2, raw/processed/features)
- une architecture Data Warehouse (PostgreSQL, modèle en étoile)
- une ingestion batch
- un streaming simulé (Kafka — sacrifiable en premier si le temps manque, cf. roadmap "Rappel — en cas de retard")
- des transformations Big Data (PySpark / DuckDB)
- des contrôles de qualité (Great Expectations / Pytest)
- du Machine Learning : forecasting, optimisation de prix, système de recommandation
- une API (FastAPI)
- un dashboard (Dash)
- du suivi de modèles (MLflow)

## Périmètre du MVP

Voir `docs/roadmap.md`. Rappel de la règle du brief : un MVP complet et fonctionnel est prioritaire sur une architecture complexe mais incomplète. En cas de retard, l'ordre de sacrifice est : infra avancée (Kafka/Airflow) puis bonus (A/B testing, CLTV, churn, XAI) — jamais les trois moteurs ML ni le dashboard.

## Personas

- **Responsable e-commerce** (seul persona explicitement nommé par le brief, section "Résultats" — destinataire du dashboard décisionnel) : consulte les KPIs globaux, le risque de rupture/surstock, le prix recommandé et les recommandations produit pour arbitrer ses décisions (achat, réassort, prix, mise en avant).
- **Category manager** (persona dérivé, non nommé explicitement dans le brief mais cohérent avec les données `category`/`subcategory`/`brand` et les KPIs pricing par catégorie) : affine les décisions de prix et de stock au niveau d'une catégorie de produits plutôt qu'au niveau global.

## Use cases

Dérivés du scénario de démonstration du brief ISM (section 50) :

1. Le responsable e-commerce ouvre le dashboard et consulte les KPIs globaux (CA, marge, commandes, stock, conversion).
2. Il consulte le stock d'un produit : la plateforme signale un risque de rupture à horizon X jours.
3. Il consulte le forecast de ce produit : le système prévoit une demande future (élevée/faible).
4. Il consulte le pricing du produit : prix actuel, prix recommandé, demande estimée, marge estimée — **toujours présentés comme des résultats sous hypothèses du modèle, jamais comme une vérité absolue**.
5. Il consulte les recommandations pour un client donné : liste de produits recommandés avec score et raison.
6. Il revient au dashboard avec les informations nécessaires pour prendre une décision (réassort, ajustement de prix, mise en avant de produits).

## KPIs

Repris du brief ISM (section 49), regroupés par domaine :

| Domaine | KPIs |
|---|---|
| Commercial | Revenue, Orders, Average Order Value, Conversion Rate |
| Marge | Gross Margin, Margin Rate, Revenue per Product |
| Stock | Current Stock, Stock Rotation, Days of Stock, Stockout Risk, Overstock Risk |
| Pricing | Current Price, Recommended Price, Price Difference, Estimated Demand, Estimated Margin, Elasticity |
| Recommendation | Precision@K, Recall@K, MAP@K, Recommendation CTR, Recommendation Conversion |

Les KPIs Commercial/Marge/Stock sont des **résultats observés** (calculables directement en SQL depuis le Data Warehouse, cf. Jalon 4). Les KPIs Pricing (hors "Current Price") et Recommendation sont des **résultats prédits/simulés** par les moteurs ML — à ne jamais présenter comme des faits observés (cf. `docs/business_case.md`).

## Critère de validation du jalon

En une phrase : *améliorer la marge, la disponibilité produit et la personnalisation d'un e-commerce local (**quel problème**), pour son responsable e-commerce (**pour qui**), à partir des transactions/comportements/promotions des trois sources UCI Online Retail II + RetailRocket + Dunnhumby Complete Journey (**avec quelles données**), en recommandant un prix, une quantité à réapprovisionner et des produits à mettre en avant pour chaque référence/client (**quelle décision**), pour réduire les ruptures/surstocks et augmenter la marge et le panier moyen (**quel impact**) — sous les hypothèses des modèles et de la simulation, jamais présenté comme une vérité absolue.

## Risques identifiés

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Volume de données RetailRocket/Dunnhumby trop lourd pour le temps disponible | Haute | Moyen | Filtrage/échantillonnage DuckDB avant tout traitement (voir data_sources.md) |
| Quotas Cloudflare R2 free tier dépassés | Moyenne | Moyen | Ne pas uploader les bruts, vérifier les quotas avant déploiement |
| Deadline serrée (6 jours) | Haute | Haut | Roadmap priorisée, infra avancée (Kafka/Airflow) sacrifiable en premier |
| Confusion données observées / synthétiques | Moyenne | Haut | Data dictionary strict, mention explicite dans le rapport |

## RGPD

Voir `docs/rgpd.md`.
