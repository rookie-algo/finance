from fastapi import Security, FastAPI, HTTPException, Query
from typing import List, Dict, Any
import yfinance as yf

from .utils.db import get_finance_transactions
from .utils.ta import calculate_position, get_exchange_rate, full_tech_analysis, get_upgrade_downgrate
from .utils.auth import validate_api_key

app = FastAPI()


@app.get("/", summary="Health Check")
def read_root() -> Dict[str, str]:
    """Simple endpoint to confirm the app is running."""
    return {"message": "Hello from FastAPI on Google App Engine!"}


# === 获取持仓 ===
@app.get("/holdings", summary="Get current holdings", tags=["Holdings"])
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
@app.get("/transactions", summary="Get all transaction records", tags=["Holdings"])
def get_transactions(api_key=Security(validate_api_key)) -> List[Dict[str, Any]]:
    """
    Retrieve all raw finance transactions as a list of dictionaries.

    Returns:
        List of transactions, where each transaction is a row from the DataFrame.
    """
    df = get_finance_transactions()
    return df.to_dict(orient="records")


# === 获取股票history Data ===
@app.get("/stock/", summary="Get stock price history and analyst rating changes", tags=["Stock"])
def get_stock(
    symbol: str = Query(..., description="Stock ticker symbol (e.g., AAPL, TSLA)")
) -> Dict[str, Any]:
    """
    Fetches 1-month daily historical stock prices and upgrade/downgrade data for a given ticker symbol.
    
    Args:
        symbol (str): The stock ticker symbol.
        
    Returns:
        Dict[str, Any]: A dictionary containing analyst upgrade/downgrade info and historical price data.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1mo", interval="1d")
        if df.empty:
            raise ValueError("No historical data found for the symbol.")

        return {
            "symbol": symbol.upper(),
            "history": df.reset_index().to_dict(orient="records"),
            "upgrades_and_downgrades": get_upgrade_downgrate(ticker)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch stock data: {str(e)}")



# === 单股技术分析 ===
@app.get("/ta/", summary="Run technical analysis on a symbol", tags=["Stock"])
def analyze_symbol(api_key=Security(validate_api_key),
                   symbol: str = Query(..., description="Ticker symbol"),
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
