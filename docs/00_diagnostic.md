# Diagnostic — 18/08/2026

## 1. Les deux documents ne sont pas équivalents

`Projet Final Gest Projet Data et E-Business.docx` est le brief pédagogique d'origine : générique, avec plusieurs options techniques laissées ouvertes (S3/MinIO ou R2, Redshift/BigQuery ou Postgres, Metabase/Superset/PowerBI/Dash/Streamlit), pensé pour un groupe de 4-5 sur 10-12 semaines.

`Projet Final ISM — Data-Driven Pricing & Recommandation.docx` est une version déjà tranchée et beaucoup plus détaillée : stack figée (Cloudflare R2, PostgreSQL, Prophet/LightGBM, FastAPI, Dash, MLflow), 12 jalons avec critères de validation, ordre de priorité explicite en cas de retard, structure de repo imposée, et une contrainte de 7 jours.

**Décision retenue pour le setup : le document ISM fait foi pour l'exécution technique** (c'est lui qui a tranché les choix d'architecture), le document Gestion de Projet fait foi pour la grille d'évaluation académique (gouvernance 15%, architecture 20%, modèles 25%, intégration 15%, business 15%, présentation 10%) — à garder en tête pour équilibrer le temps passé entre code et documentation/soutenance.

## 2. Deadline

Aujourd'hui mardi 18/08/2026. "Dimanche" est interprété comme **dimanche 23/08/2026**, soit 5 jours pleins + le reste de la journée d'aujourd'hui. Le roadmap (`docs/roadmap.md`) est calé sur ces dates. Si le rendu réel est un autre dimanche, il suffit de décaler les dates du roadmap, la structure des jalons reste valable.

## 3. Données : audit complet dans docs/data_sources.md

Résumé : les trois sources prescrites par le brief (UCI Online Retail II, RetailRocket, Dunnhumby Complete Journey) sont **toutes les trois présentes et complètes** dans `Projet Ecommerce/data`. Bonne nouvelle, c'est la partie la plus longue à retrouver/nettoyer habituellement.

Trois points de vigilance identifiés :

1. **Un dataset non prévu par le brief est présent** : Olist (e-commerce brésilien, ~127 Mo). Il n'est mentionné dans aucun des deux documents. Décision : ne pas l'utiliser pour le MVP afin de ne pas violer la règle du brief sur le mélange de sources hétérogènes ; le garder en réserve comme bonus optionnel.
2. **Deux fichiers sont très volumineux** : `item_properties_part1/2.csv` (RetailRocket, ~900 Mo cumulés) et `causal_data.csv` (Dunnhumby, ~696 Mo). Un chargement pandas naïf ferait exploser la mémoire et le temps de traitement. Le roadmap prévoit explicitement de les traiter avec DuckDB/PySpark et de différer `causal_data.csv` (peu prioritaire pour le MVP).
3. **M5 (référence forecasting) n'a pas été téléchargée.** Le brief la présente comme optionnelle — décision assumée de ne pas la chercher, pour ne pas perdre de temps sur une source secondaire.

Volumétrie totale téléchargée : environ 2,6 Go, dont une partie redondante (3 fichiers zip qui dupliquent des CSV déjà extraits, à supprimer localement pour faire de la place).

## 4. Ce qui a été mis en place dans ce setup

- Arborescence de repo conforme à la structure imposée par le brief ISM (section 30)
- `AGENTS.md` : instructions canoniques pour les agents de code (stack, règles data, règles ML, règles de code), importé par `CLAUDE.md` pour que Claude Code et Codex partagent exactement le même contexte sans duplication
- `docs/roadmap.md` : les 12 jalons du brief compressés sur 6 jours, avec dates, checklists et l'ordre de priorité en cas de retard
- `docs/data_sources.md` : l'audit ci-dessus, détaillé fichier par fichier
- Squelettes de code : générateur de données synthétiques (seed=42), Dockerfiles API/dashboard, stub FastAPI, stub de tests, workflow CI GitHub Actions
- `PROMPT_KICKOFF.md` : le prompt à coller dans Claude Code et dans Codex pour démarrer l'exécution

## 5. Intégration de l'espace Notion (accès accordé en cours de session)

L'accès a été accordé après la première tentative (BLK-001, résolu). Trois pages ont été lues : Fondations transverses, Setup Data, Setup Multi-Domaine. Ce qui a été concrètement intégré au setup :

- **Système de mémoire Claude Code** (`.claude/memory/` : decisions.md, learnings.md, blockers.md, journal.md, evals.md + `memory.sh`) — c'est l'apport le plus utile pour un projet solo étalé sur 6 jours avec deux agents (Claude Code et Codex) qui doivent partager le même contexte sans que rien ne se perde entre les sessions. `AGENTS.md` section 7 impose le rituel de lecture en début de session et de clôture en fin de session.
- **`memory.sh`** : script qui affiche les 10 derniers commits Git + la dernière entrée du journal, pour reprendre le fil en quelques secondes.
- **Environnement reproductible** : `make setup` utilise `uv` si disponible (recommandation Notion — plus rapide, lockfile fiable), avec repli automatique sur `venv`/`pip` sinon.
- **Recommandations MCP** (AGENTS.md section 8) : Postgres MCP pour l'introspection du Data Warehouse, Context7 pour la doc à jour de Prophet/LightGBM/FastAPI/Dash/MLflow, pas plus de 3 serveurs MCP actifs simultanément.
- **Réflexe sécurité avant livraison** : scan `gitleaks` et skill `gdpr-compliance-scanner` mentionnés en amont du Jalon 11, en cohérence avec `docs/rgpd.md`.

Ce qui n'a volontairement pas été repris : le processus interactif en 13 phases de la page Setup Data (une série de prompts qui interviewent l'utilisateur question par question). Il est pensé pour cadrer un projet depuis zéro sans brief existant — ici, les deux documents ISM et Gestion de Projet répondent déjà à ces questions (problématique, architecture, stack), donc relancer l'interview aurait fait perdre du temps sans rien apporter. Le contenu utile de ces 13 phases (baseline avant modèle complexe, split temporel, tests de non-régression, gouvernance data avant modélisation) était déjà présent dans le brief ISM et repris dans `AGENTS.md`.

De même, les 6 documents génériques du système de mémoire (`brand-brief.md`, `app-spec.md`, `feature-backlog.md`, `integrations.md`, `errors-log.md`) n'ont pas été dupliqués : leur contenu utile est déjà couvert par les documents spécifiques au brief (`cahier_des_charges.md`, `data_dictionary.md`, `architecture.md`) qui collent mieux à la grille d'évaluation académique que le format générique.
