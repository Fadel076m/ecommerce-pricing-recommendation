"""FastAPI — squelette (Jalon 8). Endpoints définis dans docs/api.md."""
from fastapi import FastAPI

app = FastAPI(title="Ecommerce Data-Driven Pricing & Recommandation API")


@app.get("/health")
def health():
    return {"status": "ok"}


# TODO Jalon 8 :
# GET /forecast/{product_id}
# GET /pricing/{product_id}
# GET /recommendations/{customer_id}
# POST /pricing/simulate
