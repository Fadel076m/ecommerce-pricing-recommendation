#!/usr/bin/env bash
# Restaure l'instantané de démo (demo/) : base PostgreSQL déjà peuplée +
# modèles déjà entraînés (Jalons 5-7). Permet de voir le dashboard fonctionner
# immédiatement après un `git clone`, sans re-télécharger les sources de
# données ni ré-entraîner quoi que ce soit.
#
# Usage : bash scripts/restore_demo.sh   (ou `make demo`)
set -euo pipefail
cd "$(dirname "$0")/.."

# Sur Git Bash (Windows), les arguments ressemblant à des chemins POSIX (ex.
# /tmp/...) sont réécrits en chemins Windows avant d'atteindre `docker exec` à
# l'intérieur du conteneur — sans effet sur Linux/Mac, où cette variable est
# simplement ignorée.
export MSYS_NO_PATHCONV=1

if [ ! -f .env ]; then
  echo "Copie de .env.example vers .env (valeurs de démo, aucun identifiant externe requis)..."
  cp .env.example .env
fi

echo "Démarrage de PostgreSQL et MLflow..."
docker compose up -d postgres mlflow

echo "Attente de PostgreSQL..."
until docker exec ecommerce_postgres pg_isready -U ecommerce -d ecommerce_dw > /dev/null 2>&1; do
  sleep 1
done

echo "Restauration de la base de démo (demo/warehouse_dump.dump)..."
docker cp demo/warehouse_dump.dump ecommerce_postgres:/tmp/warehouse_dump.dump
docker exec -e PGPASSWORD=devlocal_ecommerce_2026 ecommerce_postgres \
  pg_restore -U ecommerce -d ecommerce_dw --clean --if-exists --no-owner /tmp/warehouse_dump.dump

echo "Copie des modèles pré-entraînés (demo/models/) vers models/..."
mkdir -p models
cp demo/models/* models/

echo "Démarrage de l'API et du dashboard..."
docker compose up -d --build api dashboard

echo ""
echo "Prêt : Dashboard -> http://localhost:8050  |  API (Swagger) -> http://localhost:8000/docs  |  MLflow -> http://localhost:5000"
