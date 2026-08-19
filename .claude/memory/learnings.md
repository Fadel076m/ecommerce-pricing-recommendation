---
type: learnings
project: ecommerce-pricing-recommendation
---

# Patterns observés & corrections (LRN)

| ID | Date | Résumé |
|---|---|---|
| LRN-001 | 2026-08-18 | item_properties (RetailRocket) et causal_data (Dunnhumby) sont trop lourds pour pandas brut |
| LRN-002 | 2026-08-19 | `pip install -r requirements.txt` avec `apache-airflow` non contraint peut rester bloqué des heures sans erreur ni sortie |

## LRN-001 — Fichiers volumineux à ne jamais charger avec pandas brut

**Date** : 2026-08-18
**Pattern observé** : `item_properties_part1.csv` + `item_properties_part2.csv` (RetailRocket, ~900 Mo cumulés) et `causal_data.csv` (Dunnhumby, ~696 Mo) sont les deux fichiers les plus lourds du projet. Un `pandas.read_csv` naïf dessus risque de saturer la mémoire ou de ralentir excessivement l'itération.
**Contexte** : audit initial des données (voir `docs/data_sources.md`).
**Application future** : toujours passer par DuckDB (lecture filtrée/streaming) ou PySpark pour ces deux fichiers. Filtrer `item_properties` sur les `itemid` présents dans `events.csv` avant toute jointure. Différer l'ingestion de `causal_data.csv` au-delà du MVP (Jalon 6+ seulement si le temps le permet).

## LRN-002 — `apache-airflow` non contraint bloque le resolver pip silencieusement

**Date** : 2026-08-19
**Pattern observé** : un `pip install -r requirements.txt` incluant `apache-airflow>=2.9` aux côtés de fastapi/pydantic/prophet/lightgbm est resté bloqué (0 sortie, quasi 0 CPU) pendant plusieurs heures, sans message d'erreur, sans timeout naturel — seul `Get-Process` a permis de constater qu'il tournait toujours mais sans progresser.
**Contexte** : installation de l'environnement Python du Jalon 0/1 (voir BDR-004).
**Application future** : ne jamais installer `apache-airflow` dans le même `pip install` que le reste des dépendances du projet. L'isoler dans un fichier séparé et l'installer avec `--constraint <fichier de contraintes officiel Airflow correspondant à la version Python/Airflow>`. Si un `pip install` reste sans sortie pendant plus de quelques minutes sur un gros requirements.txt, vérifier `Get-Process` (CPU quasi nul = resolver bloqué, pas un téléchargement lent) avant d'attendre plus longtemps.
