# AGENTS.md — Instructions canoniques du projet

Ce fichier est la source de vérité pour tout agent de code (Claude Code, Codex CLI, ou autre) travaillant sur ce repo. `CLAUDE.md` importe ce fichier — ne dupliquez pas son contenu ailleurs, modifiez uniquement ce fichier.

## 1. Contexte du projet

Master 2 Big Data — projet final "Gestion de Projet Data & EBusiness" et "ISM — Data-Driven Pricing & Recommandation". Plateforme Big Data/IA pour un e-commerce local, permettant d'optimiser les prix, prévoir la demande, gérer les stocks et personnaliser les recommandations.

Trois moteurs à livrer : **Forecasting** (prévision de la demande), **Dynamic Pricing** (prix recommandé maximisant la marge sous hypothèses), **Recommendation System** (recommandations produits hybrides). Résultats exposés via une API FastAPI et un dashboard décisionnel Dash.

Mode de travail : solo, piloté avec Claude Code et Codex en parallèle sur le même repo. Deadline : **dimanche 23/08/2026**. Le détail des jalons datés est dans `docs/roadmap.md` — consultez-le et mettez à jour ses checkbox avant de clore une session de travail.

## 2. Stack technique imposée (ne pas dévier sans raison documentée)

| Domaine | Techno |
|---|---|
| Langage | Python |
| Data Lake | Cloudflare R2 (compatible S3, via boto3) |
| Format Data Lake | Apache Parquet |
| Big Data Processing | PySpark |
| Analytics local | DuckDB |
| Data Warehouse | PostgreSQL |
| Orchestration | Apache Airflow (si le temps le permet) |
| Streaming simulé | Apache Kafka (si le temps le permet) |
| Forecasting | Prophet / LightGBM |
| Pricing | Python + élasticité + simulation |
| Recommendation | Scikit-learn + FAISS |
| MLOps | MLflow |
| API | FastAPI |
| Dashboard | Dash + Plotly |
| Conteneurisation | Docker / docker-compose |
| Tests | Pytest |
| Data Quality | Great Expectations ou assertions Pytest |
| CI/CD | GitHub Actions |

## 3. Sources de données — règles strictes

Le détail complet (fichiers réels, poids, statut) est dans `docs/data_sources.md`. Résumé des règles non négociables :

- Trois sources utilisées : **UCI Online Retail II** (transactions/clients/produits/prix), **RetailRocket** (comportement, events + item_properties), **Dunnhumby Complete Journey** (promotions, coupons, ménages, stock synthétique).
- **Ne jamais fusionner ces sources dans une même table sans passer par le modèle de données cible.** Elles ont des identifiants, périodes et contextes différents (règle explicite du brief).
- Le dataset **Olist** est présent dans `data/` mais **hors périmètre** — ne pas l'utiliser pour le MVP, ne jamais le mélanger avec les trois sources ci-dessus.
- Le dataset **M5** n'a pas été téléchargé — c'est un choix assumé, ne pas tenter de le réintégrer sous pression de deadline.
- `item_properties_part1/2.csv` (RetailRocket, ~900 Mo) et `causal_data.csv` (Dunnhumby, ~696 Mo) sont volumineux : **ne jamais charger avec `pandas.read_csv` brut**. Utiliser DuckDB en lecture filtrée/streaming ou PySpark. `causal_data.csv` est différé (voir roadmap Jalon 6+ seulement si le temps le permet).
- Variables absentes des sources publiques (cost_price, stock, promotion, discount) sont **générées synthétiquement** via `scripts/data_generator.py` avec `random.seed(42)` — reproductible, jamais improvisé à la volée dans un notebook.
- Toute variable synthétique ou dérivée doit être identifiée comme telle dans `docs/data_dictionary.md` (colonnes : nom, type, source, signification, transformation, usage). Ne jamais présenter une donnée synthétique comme une donnée observée.
- Cloudflare R2 free tier a des quotas (stockage, opérations) : ne jamais uploader les fichiers bruts tels quels, toujours filtrer/agréger en local avant upload, ne pas réécrire inutilement les mêmes fichiers.

## 4. Règles ML — non négociables

- **Data leakage interdit.** Jamais d'information future pour prédire le passé, en particulier pour forecasting, pricing, recommendation.
- **Forecasting/Recommendation** : split **temporel**, jamais de random train/test split classique.
- **Pricing** : l'élasticité estimée n'est pas causale. Toujours formuler les résultats comme "sous les hypothèses du modèle et de la simulation" — jamais comme une vérité absolue.
- **Stock** : toujours vérifier la cohérence `closing_stock = opening_stock + stock_in - quantity_sold`.
- Chaque expérience (forecasting, pricing, recommendation) doit être loggée dans MLflow (modèle, paramètres, métriques, artefacts, version).
- Baseline obligatoire avant modèle complexe : Moving Average pour forecasting, Most Popular pour recommendation. Ne pas sauter directement au modèle sophistiqué.

## 5. Règles de code

- Structure de dossiers imposée (voir arborescence ci-dessous) — ne pas la réorganiser sans mettre à jour ce fichier.
- Un commit par jalon terminé (voir `docs/roadmap.md`), message clair en français ou anglais cohérent avec l'historique existant.
- Tests Pytest obligatoires au minimum pour : data quality, API, pricing, recommendation, transformations (section CI/CD du brief).
- `.env` ne doit jamais être commité. Seul `.env.example` est versionné.
- Le dashboard ne doit pas dupliquer de logique métier : il consomme l'API, il ne recalcule rien.
- Avant de considérer un jalon terminé, vérifier son "critère de validation" tel que défini dans `docs/roadmap.md`.

## 6. Arborescence du repo

```
ecommerce-pricing-recommendation/
├── README.md
├── AGENTS.md            # ce fichier — source de vérité pour les agents
├── CLAUDE.md             # importe AGENTS.md pour Claude Code
├── memory.sh              # affiche les derniers commits + dernière entrée du journal
├── .claude/memory/        # decisions.md, learnings.md, blockers.md, journal.md, evals.md
├── docs/                 # cahier des charges, architecture, data dictionary, sources, quality, rgpd, business case, api, roadmap
├── data/
│   ├── sample/           # échantillons nettoyés, versionnés (petits fichiers uniquement)
│   └── schemas/          # schémas Parquet / SQL
├── src/
│   ├── ingestion/        # extraction sources -> R2
│   ├── transformation/   # raw -> processed -> features
│   ├── forecasting/
│   ├── pricing/
│   ├── recommendation/
│   └── features/
├── notebooks/            # 01_eda, 02_forecasting, 03_pricing, 04_recommendation
├── api/                  # FastAPI (main.py)
├── dashboard/            # Dash (app.py)
├── tests/
├── airflow/              # DAGs (si Jalon 10 avancé)
├── docker/               # Dockerfiles
├── models/               # artefacts modèles (non versionnés)
├── scripts/              # data_generator.py, utilitaires
├── requirements.txt
├── docker-compose.yml
├── .env.example
├── .gitignore
└── .github/workflows/ci.yml
```

Note : `data/raw_local/` (non versionné, dans `.gitignore`) est l'emplacement conseillé pour travailler sur les fichiers bruts volumineux copiés depuis `Projet Ecommerce/data` sur la machine locale, avant leur passage en Parquet et leur montée sur R2.

## 7. Système de mémoire — obligatoire en début et fin de session

Ce projet utilise le système de mémoire Claude Code standard (`.claude/memory/`), pour que Claude Code et Codex ne repartent jamais de zéro d'une session à l'autre.

**En début de session**, avant toute action :
1. Lancer `./memory.sh` (ou lire directement `.claude/memory/journal.md`) pour voir où en est le projet.
2. Lire la dernière entrée de `.claude/memory/journal.md`, ainsi que `.claude/memory/learnings.md` et `.claude/memory/blockers.md` en entier (ils sont courts) — ne pas répéter une erreur déjà documentée.
3. Avant de nommer une colonne ou une table, vérifier `docs/data_dictionary.md`.

**En fin de session** (rituel de clôture, 5 minutes, à ne jamais sauter) :
1. Décidé — une décision structurante prise aujourd'hui ? → entrée dans `.claude/memory/decisions.md` (BDR-XXX).
2. Appris — un pattern observé ou une correction à ne plus refaire ? → entrée dans `.claude/memory/learnings.md` (LRN-XXX).
3. Bloqué — quelque chose qui a coûté plus de 30 minutes ? → entrée dans `.claude/memory/blockers.md` (BLK-XXX).
4. Toujours : une entrée du jour dans `.claude/memory/journal.md` (3-5 lignes factuelles + prochaine étape), même si rien d'autre n'est à ajouter.
5. Cocher les cases du jalon terminé dans `docs/roadmap.md`, puis commit.

Ne jamais créer une deuxième section mémoire ailleurs (dans `CLAUDE.md` ou un autre fichier) qui contredirait celle-ci — ce fichier est la seule source de vérité pour la mémoire du projet.

## 8. MCP et outils recommandés (à connecter côté IDE, hors périmètre de cet agent)

- **MCP PostgreSQL** : introspection de schéma automatique et exécution de requêtes SQL paramétrées sur le Data Warehouse — utile dès le Jalon 4.
- **Context7** : documentation à jour de Prophet, LightGBM, FastAPI, Dash, MLflow — préférable à la mémoire du modèle pour toute question de syntaxe/API.
- **GitHub MCP** : versioning, à connecter si les commits/PR doivent être pilotés depuis l'agent.
- Ne pas dépasser 3 serveurs MCP actifs simultanément sur ce projet (Filesystem + Postgres + Context7 suffisent) — au-delà, le modèle confond les outils similaires.
- Avant la livraison finale (Jalon 11), scanner le repo avec un outil type `gitleaks` pour vérifier qu'aucun secret n'a été commité par erreur, et envisager le skill `gdpr-compliance-scanner` pour vérifier `docs/rgpd.md` contre le code réel.

## 9. Comment travailler, jalon par jalon

1. Lire `docs/roadmap.md`, identifier le jalon en cours.
2. Lire la section correspondante dans les deux documents source du brief si besoin de détail (`Projet Final ISM — Data-Driven Pricing & Recommandation.docx` et `Projet Final Gest Projet Data et E-Business.docx`, à la racine du dossier `Projet Ecommerce`).
3. Implémenter, tester, documenter.
4. Cocher les cases du jalon dans `docs/roadmap.md`.
5. Appliquer le rituel de clôture de la section 7, puis commit.
6. Passer au jalon suivant, sans revenir en arrière sur un point déjà validé sauf bug bloquant.

## 10. Positionnement à respecter dans toute doc/présentation

Ne jamais présenter le projet comme "trois modèles de Machine Learning entraînés". Le présenter comme une plateforme décisionnelle Data-Driven de bout en bout, de la donnée brute à la décision business (chaîne Business → Data → Data Engineering → Data Science → MLOps → API → Dashboard → Décision business).
