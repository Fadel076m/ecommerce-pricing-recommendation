# Plateforme Data-Driven Pricing & Recommandation — E-commerce local

Projet final Master 2 Big Data (ISM / Gestion de Projet Data & EBusiness). Plateforme décisionnelle de bout en bout : forecasting de la demande, dynamic pricing, système de recommandation, exposés via une API FastAPI et un dashboard Dash.

## Démarrage rapide

```bash
cp .env.example .env        # puis remplir les credentials R2 / Postgres
make setup                  # crée le venv (uv si présent, sinon venv/pip) et installe les dépendances
make docker-up               # lance Postgres + MLflow
make ingest                  # pipeline d'ingestion vers R2 + Postgres
make api                     # API FastAPI sur :8000 (Swagger sur /docs)
make dashboard                # Dashboard Dash sur :8050
make memory                   # affiche les derniers commits + dernière entrée du journal de session
```

## Documentation

Toute la documentation projet est dans `docs/` :

- `docs/roadmap.md` — jalons datés, checklist, deadline
- `docs/data_sources.md` — audit réel des données disponibles
- `docs/data_dictionary.md`, `docs/data_quality.md` — modèle de données et contrôles
- `docs/architecture.md`, `docs/api.md` — architecture technique
- `docs/rgpd.md`, `docs/business_case.md` — cadrage business et conformité
- `docs/cahier_des_charges.md` — cadrage initial

## Pour les agents de code (Claude Code / Codex)

Les instructions canoniques du projet sont dans `AGENTS.md` (importé par `CLAUDE.md`). Toujours les lire avant de commencer une session de travail — voir aussi `PROMPT_KICKOFF.md` pour le prompt de démarrage.

Le projet utilise le système de mémoire Claude Code (`.claude/memory/` : décisions, apprentissages, blocages, journal, évaluations). Lancer `./memory.sh` en début de session pour reprendre le fil, et appliquer le rituel de clôture décrit dans `AGENTS.md` (section 7) en fin de session.
