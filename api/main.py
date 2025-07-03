from fastapi import FastAPI, HTTPException, Query
from typing import List, Dict, Any

from .utils.db import get_finance_transactions
from .utils.ta import calculate_position, get_exchange_rate, full_tech_analysis

app = FastAPI()


@app.get("/", summary="Health Check")
def read_root() -> Dict[str, str]:
    """Simple endpoint to confirm the app is running."""
    return {"message": "Hello from FastAPI on Google App Engine!"}


@app.get("/holdings", summary="Get current holdings")
def get_holdings() -> List[Dict[str, int]]:
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


@app.get("/ta/", summary="Run technical analysis on a symbol")
def analyze_symbol(symbol: str = Query(..., description="Ticker symbol"),
                   analyse: bool = Query(False, description="Include holding analysis")) -> Dict[str, Any]:
    """
    Returns technical analysis and optional holding metrics for a given symbol.
    """
    analysis, df, news_df = full_tech_analysis(symbol=symbol)

    if df.empty:
        raise HTTPException(status_code=400, detail=analysis)

    close_today = df.iloc[-1]["Close"]
    close_prev = df.iloc[-2]["Close"]
    change_pct = (close_today - close_prev) / close_prev * 100
    exchange_rate = get_exchange_rate()

    response = {
        "Symbol": symbol.upper(),
        "Close": float(close_today),
        "PrevClose": float(close_prev),
        "ChangePct": round(change_pct, 2),
        "Recommandation": analysis,
        "News": news_df.to_dict(orient='records'),
    }

    # If analyse=True and there are matching transactions, compute holding info
    if analyse:
        transactions_df = get_finance_transactions()
        symbol_tx = transactions_df[transactions_df["Symbol"].str.upper() == symbol.upper()]

        if not symbol_tx.empty:
            holdings = {}
            for currency, sub_df in symbol_tx.groupby("Currency"):
                shares, invested = calculate_position(sub_df)
                fx = 1 if currency == "USD" else exchange_rate
                value_now = shares * close_today / fx
                pnl = value_now - invested
                pnl_pct = (pnl / invested * 100) if invested != 0 else 0

                holdings[currency] = {
                    "Shares": int(shares),
                    "Invested": round(invested, 2),
                    "ValueToday": round(value_now, 2),
                    "PnL": round(pnl, 2),
                    "PnL_Pct": round(pnl_pct, 2),
                }

            response["Holdings"] = holdings

    return response
