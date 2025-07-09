from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

from .routes import transactions
from .routes import stock

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 👈 Or use ["http://localhost:3000"] for stricter control
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(stock.router, prefix="/api/stock", tags=["stocks"])

@app.get("/", summary="Health Check")
def read_root() -> Dict[str, str]:
    """Simple endpoint to confirm the app is running."""
    return {"message": "Hello from FastAPI on Google App Engine!"}
