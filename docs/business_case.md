# Business Case

> Première version (Jalon 1). Les chiffres réels (résultats observés/prédits/simulés) seront renseignés au fil des jalons ML (5-7) et finalisés au Jalon 11/12 — ce document pose ici la structure et les hypothèses.

À distinguer strictement (brief section 48), pour ne jamais confondre une mesure et une prévision :

## Résultats observés
Calculés directement depuis les données historiques du Data Warehouse (Jalon 4) : CA, nombre de commandes, marge historique, panier moyen, taux de rupture/surstock historique. Renseigné à partir du Jalon 4.

## Résultats prédits
Produits par les modèles entraînés (Jalon 5-7) : demande future (forecasting), prix recommandé et marge estimée (pricing), produits recommandés (recommendation). Toujours accompagnés de leurs métriques de validation (MAE/RMSE/MAPE, Precision@K/Recall@K/MAP@K) pour que leur fiabilité soit visible.

## Résultats simulés
Produits par un scénario business appliquant les résultats prédits à l'historique (Jalon 6, simulation de prix) : gain de marge potentiel, impact pricing, impact recommandations, ROI estimé. **Toujours formulés "sous les hypothèses du modèle et de la simulation"** — jamais présentés comme une performance réelle ni comme une garantie.

## Hypothèses de simulation (à documenter au fur et à mesure)

- L'élasticité prix-demande estimée en Jalon 6 n'est pas causale (corrélationnelle, sur données observationnelles) — le prix recommandé maximise une marge *estimée*, pas une marge garantie.
- Le gain de marge simulé suppose une demande qui réagit au prix comme le modèle l'a appris sur l'historique ; aucun test A/B réel n'est mené dans le cadre de ce projet (cf. `docs/roadmap.md`, bonus sacrifiable).
- Le ROI estimé combine gain de marge (pricing), réduction de rupture/surstock (forecasting) et hausse de conversion/panier moyen attribuable aux recommandations — ces effets ne sont pas isolés les uns des autres dans la simulation.

## ROI estimé

TODO — à chiffrer en Jalon 11/12 à partir des résultats mesurés des trois moteurs (métriques de validation) et des résultats simulés ci-dessus, jamais avant d'avoir les résultats réels des jalons 5-7.
