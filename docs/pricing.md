# Pricing — Jalon 6

> **Sous les hypothèses du modèle et de la simulation.** L'élasticité estimée n'est **pas causale** : c'est une régression sur données observationnelles (log-log), pas une expérimentation contrôlée (pas de test A/B). Aucun chiffre de cette page ne doit être présenté comme une vérité mesurée dans le rapport ou la soutenance.

## Méthodologie

1. **Élasticité** (`src/pricing/elasticity.py`) : régression log-log `log(quantité+1) = a + élasticité × log(prix)` par produit, sur l'historique quotidien agrégé (`fact_sales` × `dim_date`).
   - Éligibilité à l'estimation : ≥20 observations, ≥5 prix distincts, coefficient de variation du prix > 5 %.
   - **1057 produits sur 4631** sont éligibles — la grande majorité du catalogue n'a quasiment aucune variation de prix observée dans l'historique UCI, une régression y serait du bruit pur.
   - Pour les 3574 produits restants : élasticité **assumée** par défaut à **-1,5** (hypothèse documentée, pas mesurée — cf. `src/pricing/elasticity.py`).
   - Sécurité : l'élasticité estimée est bornée à `[-10, 0]` (un bien normal a une élasticité négative ou nulle ; sur un petit échantillon bruité, la régression peut ressortir un coefficient positif par pur artefact statistique — testé dans `tests/test_pricing.py`).
2. **Simulation** (`src/pricing/simulate.py`) : grille de 13 prix candidats de -30 % à +30 % autour du prix actuel, demande simulée à élasticité constante `Q(p) = Q0 × (p/p0)^élasticité`, marge estimée `= (prix - cost_price) × demande simulée`. Le prix recommandé maximise la marge estimée sur la grille.
3. Tout le pipeline (`src/pricing/train.py`) tourne sur les **4631 produits** du catalogue (élasticité estimée ou assumée) et logge dans MLflow (expérience `pricing`).

## Résultats (19/08/2026)

| | |
|---|---|
| Produits traités | 4631 |
| Élasticité estimée par régression | 1057 (23 %) |
| Élasticité assumée par défaut (-1,5) | 3574 (77 %) |
| R² médian (produits estimés) | **0,12** |
| Uplift de marge médian simulé (produits estimés) | +35,5 % |
| Uplift de marge médian simulé (produits assumés) | +38,7 % |
| Part des produits avec un changement de prix recommandé | 98,9 % |

## Limites explicites — à ne jamais omettre

- **R² médian très faible (0,12)** sur les produits où l'élasticité est réellement estimée : la relation prix/demande observée dans les données est fortement bruitée (confondue avec saisonnalité, promotions synthétiques, effets d'autres produits — aucun de ces facteurs n'est contrôlé dans cette régression bivariée simple). L'élasticité individuelle d'un produit donné ne doit pas être citée seule sans ce R².
- **77 % du catalogue** repose sur une élasticité **assumée**, pas mesurée — le prix recommandé pour ces produits reflète une hypothèse de marché générique, pas un comportement observé de leurs clients.
- **98,9 % de produits avec changement recommandé** est un signal d'alerte, pas une victoire : il reflète en grande partie le fait que `cost_price` est **synthétique** (généré avec une marge aléatoire 15-45 %, cf. `docs/data_dictionary.md`) et que `current_price` (dernier prix observé) est parfois très proche du coût synthétique — la simulation "trouve" mécaniquement de la marge à aller chercher. Ce n'est pas une opportunité business réelle mesurée sur une vraie structure de coûts.
- L'uplift de marge simulé (+35 à +39 % médian) est calculé **sur les mêmes hypothèses synthétiques** — à formuler exclusivement comme "sous les hypothèses de la simulation" dans le business case (`docs/business_case.md`), jamais comme un gain attendu réel.
