---
type: journal
project: ecommerce-pricing-recommendation
---

# Journal de session

## 2026-08-18

Setup initial du repo à partir des deux briefs (ISM + Gest Projet) et de l'audit réel des données dans `Projet Ecommerce/data`. Structure de dossiers créée, `AGENTS.md`/`CLAUDE.md` en place, roadmap daté sur 6 jours (deadline dimanche 23/08). Intégration du système de mémoire Claude Code (`.claude/memory/`, `memory.sh`) et des conventions d'environnement depuis l'espace Notion de l'utilisateur (accès accordé en cours de session). Prochaine étape : démarrer le Jalon 1 (cadrage) mercredi 19/08.

## 2026-08-19

J0 finalisé puis Jalon 1 (Cadrage) terminé. Côté infra : `.env` local créé, Postgres + MLflow up via Docker (`docker-compose.yml` nettoyé), remote GitHub `origin` ajouté et `master` poussé. L'installation Python a buté sur un `pip` bloqué plusieurs heures par `apache-airflow` non contraint (BLK-002/LRN-002) — Airflow isolé dans `requirements-airflow.txt` (BDR-004), réinstallation du cœur relancée. Côté cadrage : `docs/cahier_des_charges.md` complété (objectifs business/techniques repris du brief ISM, personas, use cases dérivés du scénario de démo, KPIs inlinés, critère de validation en une phrase, risk register), `docs/business_case.md` structuré en première version (observé/prédit/simulé + hypothèses de simulation), `docs/rgpd.md` complété avec la politique de conservation. Prochaine étape : Jalon 2 (Dataset) — `data_dictionary.md`, `scripts/data_generator.py`, échantillon dans `data/sample/`, `data_quality.md` testé.
