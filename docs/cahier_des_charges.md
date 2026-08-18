# Cahier des charges — Jalon 1

> À compléter en Jalon 1 (mercredi 19/08). Structure imposée par le brief, section "Chapitre 1 — Introduction" et "Chapitre 2 — Cadrage business".

## Problématique

Comment exploiter les données transactionnelles, comportementales, produits, prix, promotions et stocks afin d'améliorer la marge, la disponibilité des produits, la conversion et la fidélisation des clients ?

## Objectifs business

- TODO : lister et prioriser (augmenter marge, réduire ruptures/surstocks, améliorer conversion, panier moyen, cross-sell, up-sell, personnalisation)

## Objectifs techniques

- TODO : voir AGENTS.md section stack technique

## Périmètre du MVP

Voir `docs/roadmap.md`. Rappel de la règle du brief : un MVP complet et fonctionnel est prioritaire sur une architecture complexe mais incomplète.

## Personas

- TODO (ex. responsable e-commerce, category manager)

## Use cases

- TODO

## KPIs

Voir la liste complète dans le brief ISM section 49 (Commercial, Marge, Stock, Pricing, Recommendation).

## Risques identifiés

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Volume de données RetailRocket/Dunnhumby trop lourd pour le temps disponible | Haute | Moyen | Filtrage/échantillonnage DuckDB avant tout traitement (voir data_sources.md) |
| Quotas Cloudflare R2 free tier dépassés | Moyenne | Moyen | Ne pas uploader les bruts, vérifier les quotas avant déploiement |
| Deadline serrée (6 jours) | Haute | Haut | Roadmap priorisée, infra avancée (Kafka/Airflow) sacrifiable en premier |
| Confusion données observées / synthétiques | Moyenne | Haut | Data dictionary strict, mention explicite dans le rapport |

## RGPD

Voir `docs/rgpd.md`.
