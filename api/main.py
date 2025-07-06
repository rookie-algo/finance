from fastapi import FastAPI
from typing import Dict

from .routes import transactions
from .routes import stock

app = FastAPI()

app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(stock.router, prefix="/stock", tags=["stocks"])

@app.get("/", summary="Health Check")
def read_root() -> Dict[str, str]:
    """Simple endpoint to confirm the app is running."""
    return {"message": "Hello from FastAPI on Google App Engine!"}
