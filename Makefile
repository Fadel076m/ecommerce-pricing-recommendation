.PHONY: setup demo ingest verify-r2 warehouse quality forecast pricing recommend api dashboard test docker-up docker-down

setup:
	@command -v uv >/dev/null 2>&1 && uv venv .venv && . .venv/bin/activate && uv pip install -r requirements.txt || \
	(python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt)

memory:
	./memory.sh

# Démo rapide (correction/soutenance) : restaure demo/warehouse_dump.dump
# (PostgreSQL) et demo/models/ (Jalons 5-7), puis démarre API + Dashboard.
# Seul prérequis : Docker Desktop. Voir README.md.
demo:
	bash scripts/restore_demo.sh

# Jalon 3 : upload raw/processed vers Cloudflare R2 (nécessite data/raw_local/, non versionné,
# et les identifiants R2 dans .env — cf. AGENTS.md §6).
ingest:
	python3 -m src.ingestion.upload_to_r2

verify-r2:
	python3 -m src.ingestion.verify_r2

# Jalon 4 : DDL + ETL processed -> PostgreSQL.
warehouse:
	python3 -m src.transformation.load_to_postgres

quality:
	pytest tests/test_data_quality.py -v

forecast:
	python3 -m src.forecasting.train

pricing:
	python3 -m src.pricing.train

recommend:
	python3 -m src.recommendation.train

api:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

dashboard:
	python3 -m dashboard.app

test:
	pytest tests/ -v

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down
