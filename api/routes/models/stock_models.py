from enum import Enum

from pydantic import BaseModel, Field


class Operation(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class Currency(str, Enum):
    BUY = "EUR"
    SELL = "USD"


class AddTransactionRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    operation: Operation
    currency: Currency
    shares: int
    amount: float
