# Forecasting — Jalon 5

## Périmètre et décision de scope

Entraîner un modèle par produit (≈4600 références) était intraitable dans le temps imparti. Deux approches complémentaires, documentées pour ne pas être confondues :

1. **Comparaison de modèles** (Baseline / Prophet) sur la **demande quotidienne agrégée** (tous produits confondus) — Prophet ne modélise qu'une série à la fois, c'est la façon standard de le comparer à une baseline.
2. **Modèle de production** : un **LightGBM global** entraîné sur le panel produit × jour (`product_id` en feature catégorielle), qui sert `GET /forecast/{product_id}` pour n'importe quel produit (Jalon 8) sans entraîner 4600 modèles — pattern "global forecasting model", standard pour ce volume de séries.

Les deux approches ne sont **pas comparables entre elles** (granularités différentes : somme sur tous les produits vs. produit unique) — ne jamais les mettre côte à côte dans un même tableau sans préciser la granularité.

## Méthodologie

- Split **temporel strict** : 30 derniers jours en test, aucune donnée du futur dans le train. Vérifié par `tests/test_forecasting.py::test_temporal_split_has_no_leakage`.
- LightGBM : évalué en **1 pas en avant** (one-step-ahead) — les features de lag/moyenne mobile du test utilisent les vraies valeurs passées, pas des prédictions rebouclées. L'application récursive sur un horizon J+1..J+7 pour l'API est un choix d'implémentation du Jalon 8, pas mesuré ici.
- Produits filtrés à ≥30 jours de ventes observées (2961 produits retenus sur ~4600) pour éviter d'entraîner sur du pur bruit ; les produits en dessous de ce seuil sont servis par la baseline dans l'API.
- Toutes les expériences loggées dans MLflow (expérience `forecasting`), modèle LightGBM sauvegardé en artefact (`models/forecasting_lightgbm_global.txt`, non versionné).

## Résultats (19/08/2026, sous hypothèses des variables synthétiques)

| Modèle | Granularité | MAE | RMSE | MAPE |
|---|---|---|---|---|
| Baseline Moving Average (7j) | Agrégée quotidienne | 10 540 | 16 663 | 314 327 % |
| Prophet | Agrégée quotidienne | 8 066 | 15 344 | 85 553 % |
| LightGBM global (one-step-ahead) | Par produit/jour | 10,9 | 64,1 | 296 % |

**Prophet bat la baseline** sur MAE et RMSE (critère de validation du jalon) sur la série agrégée.

## Avertissement MAPE (roadmap Jalon 5)

Le MAPE explose sur les trois modèles : la demande quotidienne (agrégée comme par produit) passe fréquemment proche de 0, ce qui fait diverger un pourcentage d'erreur relatif même avec un epsilon de stabilisation au dénominateur. **MAE et RMSE sont les métriques de référence pour ce projet** ; le MAPE est conservé par transparence (et parce que la roadmap le demande) mais ne doit jamais être cité seul dans le rapport final ou la soutenance.

## Limites explicites

- Les résultats ci-dessus sont mesurés sur des **données de vente réelles (UCI Online Retail II)** mais avec des variables de stock/coût/promotion **synthétiques** en amont (Jalon 2) — la précision du forecast de demande n'est pas affectée par ces variables synthétiques (elles n'entrent pas dans les features), mais toute conclusion business qui en découlerait (ex. lien forecast/rupture de stock) hérite de cette réserve.
- Le LightGBM global n'a pas de gestion explicite des ruptures de série (produit retiré puis réintroduit) ni des nouveaux produits sans historique — ces cas retombent sur la baseline côté API.
