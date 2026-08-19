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
