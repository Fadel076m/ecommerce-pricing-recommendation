.PHONY: setup ingest quality forecast pricing recommend api dashboard test docker-up docker-down

setup:
	@command -v uv >/dev/null 2>&1 && uv venv .venv && . .venv/bin/activate && uv pip install -r requirements.txt || \
	(python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt)

memory:
	./memory.sh

ingest:
	python3 src/ingestion/run.py

quality:
	pytest tests/test_data_quality.py -v

forecast:
	python3 src/forecasting/train.py

pricing:
	python3 src/pricing/simulate.py

recommend:
	python3 src/recommendation/train.py

api:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

dashboard:
	python3 dashboard/app.py

test:
	pytest tests/ -v

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down
