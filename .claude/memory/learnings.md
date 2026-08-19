---
type: learnings
project: ecommerce-pricing-recommendation
---

# Patterns observés & corrections (LRN)

| ID | Date | Résumé |
|---|---|---|
| LRN-001 | 2026-08-18 | item_properties (RetailRocket) et causal_data (Dunnhumby) sont trop lourds pour pandas brut |
| LRN-002 | 2026-08-19 | `pip install -r requirements.txt` avec `apache-airflow` non contraint peut rester bloqué des heures sans erreur ni sortie |
| LRN-003 | 2026-08-19 | `commande \| tail -N` (sans `-f`) n'affiche rien avant l'EOF : ne pas conclure à un blocage sur cette seule base |
| LRN-004 | 2026-08-19 | Un `pip install` peut échouer en fin de course sur un verrou fichier Windows si un process Python résiduel tourne encore |
| LRN-005 | 2026-08-19 | `import great_expectations` (1.20.0) termine l'interpréteur en silence si une dépendance optionnelle (grpc, google.rpc...) manque |
| LRN-006 | 2026-08-19 | Les colonnes `object` pandas à types mixtes (int + str) font planter `to_parquet` (pyarrow) — caster en `str` avant export |
| LRN-007 | 2026-08-19 | Le `transactionid` RetailRocket n'est pas unique par ligne d'événement : plusieurs items d'un même panier le partagent |
| LRN-008 | 2026-08-19 | MLflow imprime des emojis sur stdout qui font planter tout script Python sur console Windows (cp1252) — même après un run réussi |
| LRN-009 | 2026-08-19 | Un prix à 0 (article offert) casse une régression log-log (log(0) indéfini) — filtrer les prix strictement positifs en amont |
| LRN-010 | 2026-08-19 | Un content-based qui ne score que les items déjà interagis perd son intérêt principal (recommander du cold-start) |
| LRN-011 | 2026-08-19 | Évaluer des métriques sur un dict `relevant` plus large que l'échantillon réellement recommandé dilue silencieusement les scores vers 0 |
| LRN-012 | 2026-08-19 | L'encodage catégoriel LightGBM dépend de l'ordre exact des catégories vues à l'entraînement — à persister et réutiliser tel quel à l'inférence |
| LRN-013 | 2026-08-19 | `lightgbm` a besoin de `libgomp1` (OpenMP) au runtime, absent de `python:3.11-slim` |
| LRN-014 | 2026-08-19 | Un `pip install` dans un build Docker peut timeout sur un réseau instable même avec peu de paquets — `--timeout`/`--retries` généreux évite un échec évitable |

## LRN-001 — Fichiers volumineux à ne jamais charger avec pandas brut

**Date** : 2026-08-18
**Pattern observé** : `item_properties_part1.csv` + `item_properties_part2.csv` (RetailRocket, ~900 Mo cumulés) et `causal_data.csv` (Dunnhumby, ~696 Mo) sont les deux fichiers les plus lourds du projet. Un `pandas.read_csv` naïf dessus risque de saturer la mémoire ou de ralentir excessivement l'itération.
**Contexte** : audit initial des données (voir `docs/data_sources.md`).
**Application future** : toujours passer par DuckDB (lecture filtrée/streaming) ou PySpark pour ces deux fichiers. Filtrer `item_properties` sur les `itemid` présents dans `events.csv` avant toute jointure. Différer l'ingestion de `causal_data.csv` au-delà du MVP (Jalon 6+ seulement si le temps le permet).

## LRN-002 — `apache-airflow` non contraint bloque le resolver pip silencieusement

**Date** : 2026-08-19
**Pattern observé** : un `pip install -r requirements.txt` incluant `apache-airflow>=2.9` aux côtés de fastapi/pydantic/prophet/lightgbm est resté bloqué (0 sortie, quasi 0 CPU) pendant plusieurs heures, sans message d'erreur, sans timeout naturel — seul `Get-Process` a permis de constater qu'il tournait toujours mais sans progresser.
**Contexte** : installation de l'environnement Python du Jalon 0/1 (voir BDR-004).
**Application future** : ne jamais installer `apache-airflow` dans le même `pip install` que le reste des dépendances du projet. L'isoler dans un fichier séparé et l'installer avec `--constraint <fichier de contraintes officiel Airflow correspondant à la version Python/Airflow>`. Si un `pip install` reste sans sortie pendant plus de quelques minutes sur un gros requirements.txt, vérifier `Get-Process` (CPU quasi nul = resolver bloqué, pas un téléchargement lent) avant d'attendre plus longtemps — voir aussi LRN-003, qui relativise ce diagnostic.

## LRN-003 — `commande | tail -N` masque toute sortie jusqu'à l'EOF

**Date** : 2026-08-19
**Pattern observé** : lancer un `pip install ... | tail -100` en arrière-plan ne produit **aucune** ligne de sortie tant que la commande de gauche n'a pas terminé (contrairement à `tail -f`, `tail -N` sans `-f` attend l'EOF du flux d'entrée avant d'écrire quoi que ce soit). Un fichier de sortie à 0 octet pendant des heures peut donc simplement refléter ce buffering, pas forcément un vrai blocage.
**Contexte** : diagnostic de LRN-002 (blocage `apache-airflow`) — le CPU quasi nul du process restait le seul signal fiable, la sortie vide ne l'était pas.
**Application future** : pour surveiller un process long en tâche de fond, éviter `| tail -N` seul ; utiliser `| tail -f` (avec un mécanisme de fin explicite) ou rediriger directement vers un fichier (`> log 2>&1 &`) et lire ce fichier au fur et à mesure. Ne jamais interpréter une sortie vide comme une preuve de blocage sans vérifier aussi le CPU du process (`Get-Process`).

## LRN-004 — Verrou fichier Windows en toute fin de `pip install`

**Date** : 2026-08-19
**Pattern observé** : un `pip install -r requirements.txt` a échoué à la toute dernière étape (`Could not install packages due to an OSError: [WinError 32] ... utilisé par un autre processus`) sur un fichier `numpy`, alors que la quasi-totalité des paquets s'était déjà installée. Deux process Python résiduels (d'un test d'import précédent) tournaient encore et tenaient probablement le verrou.
**Contexte** : installation de l'environnement du Jalon 2, juste après le passage au venv Python 3.12.
**Application future** : avant de relancer un `pip install` qui a échoué sur un `WinError 32`, vérifier `Get-Process | Where ProcessName -like '*python*'` et tuer les process résiduels avant de relancer — `pip install` est idempotent et reprend vite grâce à son cache de wheels, il suffit généralement de relancer une fois le verrou levé.

## LRN-005 — `great_expectations` peut terminer le process en silence

**Date** : 2026-08-19
**Pattern observé** : `import great_expectations` (v1.20.0) provoque un `sys.exit(0)` silencieux (aucune exception, aucun traceback) dès qu'une dépendance optionnelle liée au télémétrie/doctest (`grpc`, puis `google.rpc` une fois `grpc` installé) est absente. Un script qui importe ce module en tête de fichier s'arrête net à cette ligne, sans message d'erreur exploitable au premier abord (juste "Skipping doctests: No module named 'X'" sur stderr).
**Contexte** : smoke test de l'environnement Python après installation (Jalon 2) — voir BDR-006.
**Application future** : si un script Python se termine silencieusement (code de sortie 0) sans exécuter la suite attendue, suspecter un import qui appelle `sys.exit()`/`os._exit()` en effet de bord, et bisecter les imports un par un plutôt que de chercher une exception qui n'existera pas. Pour ce projet : `great_expectations` n'est plus une dépendance (BDR-006), data quality en Pytest uniquement.

## LRN-006 — Colonnes `object` à types mixtes -> `to_parquet` plante (pyarrow)

**Date** : 2026-08-19
**Pattern observé** : `online_retail_II.xlsx` a des colonnes (`Invoice`/`StockCode`/`Description`) où pandas infère `dtype=object` mais où les valeurs réelles mélangent `int` et `str` sur les deux feuilles du fichier (ex. `Description` majoritairement du texte mais avec quelques valeurs numériques résiduelles). `DataFrame.to_parquet()` échoue alors avec `pyarrow.lib.ArrowInvalid`/`ArrowTypeError` ("Could not convert ... tried to convert to int64" ou "Expected bytes, got a 'int' object"), sans indiquer clairement quelle ligne pose problème.
**Contexte** : upload du layer `raw/` vers R2 (Jalon 3) — la donnée UCI brute n'a jamais ce problème pour pandas seul (il affiche juste `dtype=object`), il n'apparaît qu'au moment de la conversion Arrow.
**Application future** : avant tout `to_parquet()` sur un DataFrame venant d'une source externe non typée (xlsx/csv), caster explicitement toutes les colonnes `object` en `str` (`df[col].astype(str)` pour `df.select_dtypes(include="object").columns`) — plus fiable que de corriger colonne par colonne après coup.

## LRN-007 — `transactionid` RetailRocket n'est pas une clé de ligne unique

**Date** : 2026-08-19
**Pattern observé** : dans `events.csv` (RetailRocket), un même `transactionid` (événement `transaction`) peut apparaître sur plusieurs lignes — un panier avec plusieurs articles achetés génère une ligne par item, toutes avec le même `transactionid`. L'utiliser comme identifiant unique de ligne (`event_id`) provoque une violation de contrainte `UNIQUE`/`PRIMARY KEY` au chargement en base (`psycopg2.errors.UniqueViolation`), qui n'apparaît qu'après avoir déjà inséré des centaines de milliers de lignes.
**Contexte** : construction de `fact_web_events` (Jalon 3/4, `src/transformation/web_events.py`) — voir aussi `docs/data_dictionary.md`.
**Application future** : pour un `event_id` garanti unique sur ce type de log d'événements, préférer un identifiant positionnel (index de ligne après tri stable) plutôt qu'une combinaison de colonnes métier, même quand une colonne "id" existe dans la source — vérifier son unicité réelle avant de s'y fier (`df[col].is_unique`, pas juste "ça s'appelle id").

## LRN-008 — MLflow + console Windows (cp1252) = crash après un run réussi

**Date** : 2026-08-19
**Pattern observé** : `mlflow.start_run()` imprime sur stdout des messages contenant des emojis (🏃 pour le lien du run, 🧪 pour l'expérience) à la fin du `with` block. Sur une console Windows dont l'encodage par défaut est `cp1252` (pas UTF-8), `sys.stdout.write(...)` lève `UnicodeEncodeError` — le script plante avec un traceback qui pointe vers MLflow, alors que l'entraînement et le logging des métriques ont déjà réussi (visible dans les lignes de sortie juste avant le crash).
**Contexte** : premier lancement de `src/forecasting/train.py` (Jalon 5) — se reproduira sur tout futur script Python qui utilise MLflow en console Windows (pricing, recommendation, Jalons 6-7).
**Application future** : au tout début de tout script qui importe `mlflow` et tourne potentiellement sur console Windows, forcer l'encodage stdout/stderr en UTF-8 avant l'import (`sys.stdout.reconfigure(encoding="utf-8", errors="replace")` si `sys.platform == "win32"`). Si un script MLflow plante avec un `UnicodeEncodeError` pointant vers `_log_url`, ce n'est presque jamais un vrai échec du run — vérifier d'abord les lignes de sortie précédentes avant de re-déboguer la logique métier.

## LRN-009 — `log(0)` casse une régression log-log sans message clair

**Date** : 2026-08-19
**Pattern observé** : `fact_sales.unit_price` peut valoir exactement 0 (article offert / remise à 100 %, valide selon `docs/data_quality.md` qui n'exige que `unit_price >= 0`). Une régression log-log (`np.polyfit` sur `log(prix)`) plante alors avec `numpy.linalg.LinAlgError: SVD did not converge`, précédé de `RuntimeWarning: divide by zero encountered in log` — le message ne pointe pas directement vers la cause (une seule ligne à prix 0 suffit à casser tout le fit).
**Contexte** : estimation de l'élasticité prix-demande (Jalon 6, `src/pricing/elasticity.py`).
**Application future** : avant tout calcul en log sur une colonne prix/quantité qui peut légitimement contenir des zéros (remise à 100 %, article offert), filtrer les valeurs strictement positives en amont plutôt que de découvrir le crash à l'exécution sur données réelles — les tests unitaires sur données synthétiques ne le révèlent pas si elles ne couvrent pas ce cas limite.

## LRN-010 — Content-based limité aux items déjà interagis = perd son intérêt

**Date** : 2026-08-19
**Pattern observé** : une première version de `build_category_item_popularity` (recommendation, Jalon 7) faisait un `merge(train_interactions, item_categories, how="inner")` — ne gardant que les items ayant déjà des interactions. Un test synthétique volontairement construit avec un item catalogué mais jamais interagi (`I4`) a révélé qu'il ne pouvait jamais être recommandé, alors que c'est exactement le cas d'usage où le content-based devrait surpasser le collaborative filtering (cold-start item).
**Contexte** : `src/recommendation/content_based.py`, détecté par `tests/test_recommendation.py::test_recommend_content_based_favors_visitor_top_category`.
**Application future** : pour un module content-based, toujours partir du catalogue complet des items avec attributs connus (pas seulement ceux déjà interagis) et attribuer un score de base non nul aux items sans historique — sinon le module dégénère en une simple popularité par catégorie, sans aucun avantage sur le cold-start par rapport à la baseline. Un test avec un item délibérément sans interaction est un bon moyen de vérifier cette propriété.

## LRN-011 — Évaluer sur un `relevant` plus large que l'échantillon recommandé dilue les métriques

**Date** : 2026-08-19
**Pattern observé** : dans `src/recommendation/train.py`, un échantillon de 5000 visiteurs était utilisé pour générer les recommandations (`baseline_recs`, `content_recs`, ...), mais la fonction d'évaluation recevait `test_relevant` complet (22211 visiteurs). Pour les ~17000 visiteurs absents des dicts de recommandations, `.get(visitor_id, [])` renvoyait une liste vide, comptée comme précision/rappel = 0 dans la moyenne — les métriques rapportées (~0,0002-0,0004) étaient near 5x plus basses que la réalité (~0,001-0,006 après correction), sans qu'aucune erreur ne se déclenche.
**Contexte** : premier run du pipeline recommendation (Jalon 7) — l'incohérence n'a été repérée qu'en comparant `n_visitors_evaluated` (22211) au nombre de visiteurs réellement échantillonnés (5000) dans les logs.
**Application future** : quand une évaluation tourne sur un sous-échantillon (scoping pour tenir le temps imparti), toujours restreindre explicitement le dict "vérité terrain" au même sous-échantillon avant de calculer les métriques — et vérifier que `n_visitors_evaluated` (ou équivalent) dans la sortie correspond bien à la taille de l'échantillon voulu, pas à une population plus large silencieusement réintroduite.

## LRN-012 — L'encodage catégoriel LightGBM doit être persisté et réutilisé à l'identique

**Date** : 2026-08-19
**Pattern observé** : LightGBM encode une feature `categorical_feature` en codes entiers internes dérivés de l'ordre des catégories vues à l'entraînement (`pd.Categorical.cat.categories`). Si l'inférence reconstruit ce `Categorical` avec un ordre différent (ex. recalculé à partir d'une autre requête SQL, ou d'un sous-ensemble), les codes ne correspondent plus aux mêmes produits — le modèle donnerait des prédictions silencieusement fausses, sans aucune erreur.
**Contexte** : préparation de l'inférence forecasting pour l'API (Jalon 8, `src/forecasting/predict.py`) — repéré avant que le bug ne se produise, en réfléchissant à la reconstruction du `Categorical` côté service.
**Application future** : pour tout modèle avec une feature catégorielle (LightGBM, CatBoost, etc.), persister la liste ORDONNÉE exacte des catégories utilisées à l'entraînement (ex. `.parquet` dédié) et la charger telle quelle à l'inférence — ne jamais la recalculer indépendamment, même si le contenu semble identique.

## LRN-013 — `lightgbm` nécessite `libgomp1` sur une image Docker slim

**Date** : 2026-08-19
**Pattern observé** : le conteneur API plantait au démarrage avec `OSError: libgomp.so.1: cannot open shared object file: No such file or directory` en important `lightgbm`, alors que l'installation pip s'était bien déroulée. `python:3.11-slim` (Debian minimal) n'inclut pas la bibliothèque runtime OpenMP (`libgomp1`) dont dépend l'extension C++ de LightGBM.
**Contexte** : premier lancement du conteneur `ecommerce_api` (Jalon 8).
**Application future** : toute image Docker slim/Debian qui importe `lightgbm` (ou d'autres libs C++ compilées avec OpenMP) doit installer `libgomp1` via `apt-get install` avant l'étape `pip install` — l'erreur n'apparaît qu'au runtime (import), jamais au moment du build pip.

## LRN-014 — `pip install` peut timeout dans un build Docker même avec peu de paquets

**Date** : 2026-08-19
**Pattern observé** : `pip install -r requirements-api.txt` (une dizaine de paquets légers) a échoué deux fois de suite avec `ReadTimeoutError` sur `files.pythonhosted.org`, avant de réussir à la troisième tentative — indépendamment de la taille des paquets, donc pas un problème de gros téléchargement (contrairement à LRN précédents sur pyspark/prophet) mais de latence/instabilité réseau ponctuelle du poste vers PyPI depuis le contexte Docker build.
**Contexte** : build de l'image `ecommerce_api` (Jalon 8).
**Application future** : ajouter systématiquement `--timeout 100 --retries 10` (ou équivalent) à tout `pip install` dans un Dockerfile, même pour une liste de dépendances courte — ça ne coûte rien en cas de réseau stable et évite un échec de build entièrement transitoire.
