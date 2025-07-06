from fastapi import APIRouter, Security
from typing import List, Dict, Any

from ..utils.db import get_finance_transactions, add_transaction
from ..utils.auth import validate_api_key
from .models.stock_models import AddTransactionRequest


router = APIRouter()


# === 获取持仓 ===
@router.get("/holdings", summary="Get current holdings", tags=["Holdings"])
def get_holdings(api_key=Security(validate_api_key)) -> List[Dict[str, int]]:
    """Aggregates current holdings per symbol based on transactions."""
    transactions_df = get_finance_transactions()
    results = []

    for symbol, tx_group in transactions_df.groupby("Symbol"):
        total_shares = 0
        for operation, ops_df in tx_group.groupby("Operation"):
            shares = ops_df["Num_of_Shares"].sum()
            if operation == "BUY":
                total_shares += shares
            else:
                total_shares -= shares

        if total_shares > 0:
            results.append({symbol: int(total_shares)})

    return results


# === 获取购买记录 ===
@router.get("/history", summary="Get all transaction records", tags=["Holdings"])
def get_transactions(api_key=Security(validate_api_key)) -> List[Dict[str, Any]]:
    """
    Retrieve all raw finance transactions as a list of dictionaries.

    Returns:
        List of transactions, where each transaction is a row from the DataFrame.
    """
    df = get_finance_transactions()
    return df.to_dict(orient="records")


@router.post("/add", summary="Add transaction record", tags=["Holdings"])
def add_transactions(data: AddTransactionRequest, api_key=Security(validate_api_key)):
    success, item = add_transaction(
        data.symbol, num_of_shares=data.shares,
        amount=data.amount, operation=data.operation,
        currency=data.currency)
    content = {'success': success}
    if success:
        content['item'] = item
    return content