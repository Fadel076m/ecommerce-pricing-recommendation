---
type: journal
project: ecommerce-pricing-recommendation
---

# Journal de session

## 2026-08-18

Setup initial du repo à partir des deux briefs (ISM + Gest Projet) et de l'audit réel des données dans `Projet Ecommerce/data`. Structure de dossiers créée, `AGENTS.md`/`CLAUDE.md` en place, roadmap daté sur 6 jours (deadline dimanche 23/08). Intégration du système de mémoire Claude Code (`.claude/memory/`, `memory.sh`) et des conventions d'environnement depuis l'espace Notion de l'utilisateur (accès accordé en cours de session). Prochaine étape : démarrer le Jalon 1 (cadrage) mercredi 19/08.

## 2026-08-19

J0 finalisé puis Jalon 1 (Cadrage) terminé. Côté infra : `.env` local créé, Postgres + MLflow up via Docker (`docker-compose.yml` nettoyé), remote GitHub `origin` ajouté et `master` poussé. L'installation Python a buté sur un `pip` bloqué plusieurs heures par `apache-airflow` non contraint (BLK-002/LRN-002) — Airflow isolé dans `requirements-airflow.txt` (BDR-004), réinstallation du cœur relancée. Côté cadrage : `docs/cahier_des_charges.md` complété (objectifs business/techniques repris du brief ISM, personas, use cases dérivés du scénario de démo, KPIs inlinés, critère de validation en une phrase, risk register), `docs/business_case.md` structuré en première version (observé/prédit/simulé + hypothèses de simulation), `docs/rgpd.md` complété avec la politique de conservation. Commit `b1f5e79` poussé sur GitHub (repo créé par l'utilisateur en cours de session : https://github.com/Fadel076m/ecommerce-pricing-recommendation).

Jalon 2 (Dataset) terminé dans la foulée. Venv recréé en Python 3.12 (le 3.14 par défaut faisait exploser les temps de build de pyspark/prophet/lightgbm/faiss-cpu, BDR-005) ; `great_expectations` abandonné après un `sys.exit()` silencieux à l'import sur dépendance optionnelle manquante (BDR-006/LRN-005), data quality en Pytest uniquement (AGENTS.md l'autorise explicitement). `docs/data_dictionary.md` rempli pour les 7 tables du modèle en étoile (statuts observé/dérivé/synthétique explicites, note sur les espaces d'identifiants UCI vs RetailRocket jamais fusionnés). `scripts/data_generator.py` rendu opérationnel : charge `data/raw_local/online_retail_II.xlsx` (copié depuis `Projet Ecommerce/data`, non versionné), nettoie (1 067 371 → 779 495 lignes), génère cost_price/stock/promotion (seed=42) et exporte un échantillon dans `data/sample/` (103 044 lignes fact_sales, 4 160 produits). 9 tests Pytest passent (`tests/test_data_quality.py`), dont 3 d'intégration sur l'échantillon réel. Prochaine étape : J2 (jeudi 20/08) — Jalon 3 (Data Lake R2) + Jalon 4 (Data Warehouse PostgreSQL).
