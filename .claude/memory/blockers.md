---
type: blockers
project: ecommerce-pricing-recommendation
---

# Frictions & blocages (BLK)

| ID | Date | Résumé | Statut |
|---|---|---|---|
| BLK-001 | 2026-08-18 | Page Notion de setup initialement inaccessible (connecteur non autorisé) | résolu |
| BLK-002 | 2026-08-19 | `pip install -r requirements.txt` bloqué plusieurs heures à cause d'`apache-airflow` non contraint | résolu |

## BLK-001 — Page Notion de setup initialement inaccessible

**Date** : 2026-08-18
**Friction** : la page Notion "Setup projet dev web/mobile/Data/IA avec Claude Code" était inaccessible en début de session (connecteur Notion sans les droits sur ce workspace).
**Cause réelle** : accès non encore accordé côté utilisateur au moment du premier essai.
**Solution** : l'utilisateur a accordé l'accès en cours de session ; les pages Fondations transverses, Setup Data et Setup Multi-Domaine ont ensuite été lues et intégrées (système de mémoire `.claude/memory/`, conventions d'environnement, recommandations MCP/sécurité).
**Statut** : résolu.

## BLK-002 — `pip install` bloqué par `apache-airflow` non contraint

**Date** : 2026-08-19
**Friction** : lancé en fin de J0 (18/08 23:57), le `pip install -r requirements.txt` complet (incluant `apache-airflow>=2.9`) était toujours "running" sans aucune sortie le lendemain matin (19/08) — plusieurs heures perdues avant de détecter le blocage.
**Cause réelle** : le resolver de dépendances de pip tente de concilier l'arbre de dépendances massif d'Airflow avec fastapi/pydantic/prophet/lightgbm du reste du projet, sans jamais converger ni échouer explicitement (voir LRN-002).
**Solution** : process tué manuellement (`Stop-Process`), Airflow extrait dans `requirements-airflow.txt` séparé avec instruction d'installation via fichier de contraintes officiel (voir BDR-004), puis `pip install -r requirements.txt` relancé sans Airflow.
**Statut** : résolu.
