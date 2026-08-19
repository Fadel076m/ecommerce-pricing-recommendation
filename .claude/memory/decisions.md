---
type: decisions
project: ecommerce-pricing-recommendation
---

# Décisions structurantes (BDR)

| ID | Date | Titre | Statut |
|---|---|---|---|
| BDR-001 | 2026-08-18 | ISM fait foi pour la technique, Gest Projet pour l'évaluation | actif |
| BDR-002 | 2026-08-18 | Trois sources data uniquement (UCI, RetailRocket, Dunnhumby), Olist écarté | actif |
| BDR-003 | 2026-08-18 | M5 non téléchargée, écartée volontairement | actif |
| BDR-004 | 2026-08-19 | Airflow isolé dans `requirements-airflow.txt`, installé séparément avec contraintes officielles | actif |
| BDR-005 | 2026-08-19 | venv Python 3.12 (pas 3.14) pour la compatibilité des wheels ML | actif |
| BDR-006 | 2026-08-19 | `great_expectations` retiré du projet, data quality en Pytest uniquement | actif |
| BDR-007 | 2026-08-19 | `fact_inventory` = un instantané par produit, pas une série temporelle quotidienne | actif |
| BDR-008 | 2026-08-19 | Lecture R2 en DuckDB via secret `TYPE s3` générique (endpoint explicite), pas `TYPE r2` | actif |
| BDR-009 | 2026-08-19 | Forecasting : comparaison Baseline/Prophet sur la demande agrégée + LightGBM global par produit (pas un Prophet par produit) | actif |
| BDR-010 | 2026-08-19 | Pricing : élasticité estimée seulement si éligible (1057/4631 produits), fallback assumé -1,5 sinon, bornée à [-10,0] | actif |
| BDR-011 | 2026-08-19 | Recommendation construite entièrement dans l'espace RetailRocket (visitor_id/item_id), pas UCI customer_id | actif |

## BDR-001 — ISM fait foi pour la technique, Gest Projet pour l'évaluation

**Date** : 2026-08-18
**Décision** : le document "Projet Final ISM — Data-Driven Pricing & Recommandation" est la référence pour tous les choix d'architecture et la stack technique. Le document "Projet Final Gest Projet Data et E-Business" reste la référence pour la grille d'évaluation académique (gouvernance 15%, architecture 20%, modèles 25%, intégration 15%, business 15%, présentation 10%).
**Pourquoi** : les deux documents décrivent le même projet mais le premier est une version déjà tranchée (stack figée, jalons datés, ordre de priorité), le second est le brief générique d'origine avec plusieurs options laissées ouvertes.
**Alternatives considérées** : suivre uniquement le brief générique (rejeté — trop d'ambiguïté technique pour tenir 6 jours) ; fusionner les deux sans hiérarchie (rejeté — risque d'incohérence entre choix techniques).
**Statut** : actif.

## BDR-002 — Trois sources data uniquement, Olist écarté

**Date** : 2026-08-18
**Décision** : n'utiliser que UCI Online Retail II, RetailRocket et Dunnhumby Complete Journey. Le dataset Olist (téléchargé mais absent des deux briefs) n'est pas intégré au MVP.
**Pourquoi** : le brief interdit explicitement de mélanger des sources hétérogènes sans modèle de données cohérent (section 13 du brief ISM). Olist n'a pas d'identifiants ni de période compatibles avec les trois sources prescrites.
**Alternatives considérées** : utiliser Olist en remplacement d'une des trois sources prescrites (rejeté — non conforme au brief) ; l'intégrer comme quatrième source (rejeté — risque de confusion, hors périmètre noté).
**Statut** : actif — à révision seulement si le temps permet un enrichissement bonus après le Jalon 9.

## BDR-003 — M5 non téléchargée, écartée volontairement

**Date** : 2026-08-18
**Décision** : ne pas télécharger ni utiliser le dataset M5 (Walmart), présenté comme référence forecasting optionnelle dans le brief.
**Pourquoi** : gain de temps sur un délai de 6 jours, la source est explicitement facultative dans le brief.
**Alternatives considérées** : l'intégrer comme benchmark séparé (rejeté pour l'instant, faute de temps).
**Statut** : actif.

## BDR-004 — Airflow isolé de `requirements.txt`

**Date** : 2026-08-19
**Décision** : retirer `apache-airflow` de `requirements.txt` principal, le déplacer dans `requirements-airflow.txt` avec un exemple d'installation utilisant le fichier de contraintes officiel Airflow (`--constraint https://raw.githubusercontent.com/apache/airflow/constraints-X.Y.Z/constraints-3.11.txt`).
**Pourquoi** : un `pip install -r requirements.txt` incluant `apache-airflow>=2.9` non contraint est resté bloqué plusieurs heures (voir LRN-002) — le resolver pip tente de concilier l'immense arbre de dépendances d'Airflow avec fastapi/pydantic/prophet du reste du projet. Airflow est de toute façon explicitement sacrifiable en premier (AGENTS.md §9, roadmap "Rappel — en cas de retard").
**Alternatives considérées** : figer une version précise d'Airflow dans le même fichier (rejeté — le conflit vient de la combinaison avec les autres paquets, pas seulement de la version) ; abandonner Airflow entièrement (rejeté — encore possible si le temps le permet en fin de projet, Jalon 10).
**Statut** : actif.

## BDR-005 — venv Python 3.12 plutôt que 3.14

**Date** : 2026-08-19
**Décision** : créer le venv du projet avec Python 3.12 (`py -3.12 -m venv .venv`) plutôt qu'avec le Python 3.14 par défaut de la machine (`py -0p` le montre marqué `*`, donc défaut du `py launcher`).
**Pourquoi** : sur le venv 3.14, l'installation de `pyspark`/`prophet`/`lightgbm`/`faiss-cpu` a nécessité des heures et des builds de wheels depuis les sources (Python 3.14 sorti trop récemment pour avoir des wheels précompilés pour tout l'écosystème ML). Sur 3.12, les mêmes paquets ont des wheels précompilés Windows et s'installent en quelques minutes.
**Alternatives considérées** : garder 3.14 et attendre les builds sources (rejeté — trop lent pour un délai de 6 jours) ; Python 3.11 (non nécessaire, 3.12 a suffi).
**Statut** : actif.

## BDR-006 — `great_expectations` retiré, data quality en Pytest uniquement

**Date** : 2026-08-19
**Décision** : ne pas utiliser `great_expectations` dans le projet ; toutes les règles de data quality (`docs/data_quality.md`) sont implémentées en assertions Pytest (`tests/test_data_quality.py`).
**Pourquoi** : `import great_expectations` (v1.20.0) termine silencieusement l'interpréteur Python (`sys.exit(0)`, sans traceback) dès qu'une dépendance optionnelle (`grpc`, puis `google.rpc`...) est absente — un import en apparence anodin qui coupe tout le script qui l'utilise. AGENTS.md autorise explicitement "Great Expectations **ou** assertions Pytest" (§2) : Pytest est retenu comme seule option pour éviter cette fragilité, sans perte de couverture (9 tests passent, dont 3 d'intégration sur l'échantillon réel).
**Alternatives considérées** : traquer et installer chaque dépendance optionnelle manquante une par une (rejeté — pas de garantie que la liste s'arrête, perte de temps) ; épingler une version antérieure de `great_expectations` (non testé, risque similaire).
**Statut** : actif.

## BDR-007 — `fact_inventory` : instantané par produit, pas de série temporelle quotidienne

**Date** : 2026-08-19
**Décision** : générer une seule ligne de stock synthétique par produit (`date_id` = dernière date observée dans `fact_sales`), plutôt qu'une ligne par produit et par jour.
**Pourquoi** : le grain `(product_id, date_id)` documenté dans le brief suggère un historique quotidien complet, mais le générer pour ~4600 produits × ~740 jours (~3,4M lignes synthétiques) n'apporte rien de plus pour les cas d'usage MVP (risque de rupture/surstock au dashboard, section 50 étape 2) qu'un instantané courant, et coûte du temps de génération/chargement sur un projet de 6 jours. Documenté explicitement dans `docs/data_dictionary.md` pour ne pas être confondu avec un vrai historique.
**Alternatives considérées** : générer un historique quotidien complet (rejeté — volumétrie et temps disproportionnés par rapport au gain) ; ne pas avoir de `date_id` du tout dans `fact_inventory` (rejeté — casse la jointure `dim_date` prévue par le modèle en étoile).
**Statut** : actif — à révision si le forecasting (Jalon 5) a besoin d'un historique de stock quotidien réel.

## BDR-008 — Lecture R2 en DuckDB via secret `TYPE s3` générique

**Date** : 2026-08-19
**Décision** : pour lire les fichiers R2 depuis DuckDB, utiliser `CREATE SECRET (TYPE s3, ENDPOINT '<compte>.r2.cloudflarestorage.com', URL_STYLE 'path', REGION 'auto', ...)` plutôt que le type dédié `TYPE r2` (qui accepte `ACCOUNT_ID` au lieu d'`ENDPOINT`).
**Pourquoi** : `TYPE r2` avec `ACCOUNT_ID` renvoie une erreur HTTP 404 sur `read_parquet('s3://bucket/...')` avec ce bucket, alors que le type `s3` générique avec un `ENDPOINT` explicite et `URL_STYLE 'path'` fonctionne immédiatement (testé avec duckdb 1.5.5). Cause exacte non investiguée plus loin (possible dérivation d'URL différente entre les deux types de secret) — retenir la solution qui marche plutôt que creuser, vu le temps disponible.
**Alternatives considérées** : passer par boto3/pandas pour toute lecture R2 (rejeté — perd l'intérêt de DuckDB pour l'analyse SQL directe sur Parquet distant, exigé par le brief section 9).
**Statut** : actif.

## BDR-009 — Forecasting : comparaison sur l'agrégé, production en modèle global

**Date** : 2026-08-19
**Décision** : comparer Baseline Moving Average et Prophet uniquement sur la demande quotidienne **agrégée** (tous produits), et entraîner un **unique** modèle LightGBM "global" (panel produit × jour, `product_id` en feature catégorielle) pour servir `/forecast/{product_id}` pour n'importe lequel des ~4600 produits.
**Pourquoi** : Prophet ne modélise qu'une série à la fois — entraîner un Prophet par produit (4600 modèles) était intraitable dans le temps du projet. Le pattern "modèle global" (un seul modèle, l'identité de la série en feature) est l'approche standard pour ce volume de séries et permet de répondre à l'API pour tout produit sans réentraînement par référence.
**Alternatives considérées** : Prophet sur un échantillon de top-N produits (rejeté — n'aurait couvert qu'une fraction du catalogue pour l'API) ; un modèle LightGBM par produit (rejeté — même problème de scalabilité que Prophet, en pire).
**Statut** : actif. Les deux résultats (agrégé vs par-produit) ne sont pas comparables entre eux — documenté explicitement dans `docs/forecasting.md` pour ne pas induire en erreur au moment du rapport/soutenance.

## BDR-010 — Pricing : élasticité éligible ou fallback assumé, bornée

**Date** : 2026-08-19
**Décision** : n'estimer l'élasticité par régression log-log que pour les produits ayant ≥20 observations, ≥5 prix distincts et un coefficient de variation du prix >5 % (1057/4631 produits) ; les autres reçoivent une élasticité **assumée** par défaut (-1,5, documentée comme hypothèse, pas une mesure). Dans les deux cas, l'élasticité est bornée à `[-10, 0]` avant d'entrer dans la simulation de prix.
**Pourquoi** : un audit SQL préalable a montré que la grande majorité du catalogue UCI n'a quasiment aucune variation de prix historique — une régression y serait du pur bruit. Sur les produits éligibles eux-mêmes, le R² médian mesuré est très faible (0,12) et quelques régressions sortent des coefficients positifs par artefact statistique (bien "normal" attendu à élasticité négative) — sans bornage, cela inverserait le sens de la recommandation de prix pour ces produits.
**Alternatives considérées** : régression pooled avec effets fixes produit/catégorie (rejeté — plus robuste en théorie mais complexité et temps disproportionnés pour un R² qui resterait probablement faible faute de vraie variation exogène de prix) ; ne pas fixer de bornes (rejeté après avoir constaté des élasticités positives en sortie de régression brute).
**Statut** : actif. Le R² médian faible (0,12) et le fallback à 77 % du catalogue sont documentés en clair dans `docs/pricing.md`, jamais présentés comme des résultats fiables sans réserve.

## BDR-011 — Recommendation dans l'espace RetailRocket, pas UCI

**Date** : 2026-08-19
**Décision** : construire tout le moteur de recommandation (baseline, content-based, collaborative, hybride) dans l'espace d'identifiants RetailRocket (`visitor_id`/`item_id`), et documenter que `/recommendations/{customer_id}` (Jalon 8) doit être compris comme prenant un `visitor_id` RetailRocket, pas un `customer_id` UCI.
**Pourquoi** : le signal comportemental explicitement demandé par la roadmap Jalon 7 (view/add_to_cart/purchase) n'existe que dans RetailRocket — UCI Online Retail II n'a que des transactions complétées, pas de navigation. Fusionner artificiellement les deux espaces d'identifiants (ex. mapper un `customer_id` UCI vers un `visitor_id` RetailRocket au hasard) violerait la règle explicite du brief sur le mélange de sources hétérogènes (AGENTS.md §3) et produirait des recommandations sans aucune base réelle.
**Alternatives considérées** : construire un moteur de recommandation "purchase-only" dans l'espace UCI (customer_id/product_id, en utilisant les achats comme seul signal implicite) pour coller à l'API telle que rédigée (rejeté — perd tout le signal view/add_to_cart explicitement demandé par la roadmap, et le catalogue UCI n'a pas d'attributs produits assez riches pour un vrai content-based) ; inventer un mapping customer_id<->visitor_id (rejeté — fabriquerait une fausse donnée, contraire à AGENTS.md).
**Statut** : actif. Limite structurelle documentée dans `docs/recommendation.md` et `docs/api.md`, à rappeler explicitement dans le rapport final et la démo (Jalon 11/12) pour ne jamais laisser croire que les deux customer_id se recoupent.
