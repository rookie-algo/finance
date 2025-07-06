from fastapi import APIRouter, Query, Security, HTTPException
from typing import Dict, Any

import yfinance as yf

from ..utils.ta import calculate_position, get_exchange_rate, full_tech_analysis, get_upgrade_downgrate
from ..utils.db import get_finance_transactions
from ..utils.auth import validate_api_key


router = APIRouter()


# === 获取股票history Data ===
@router.get("/history/", summary="Get stock price history and analyst rating changes", tags=["Stock"])
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
@router.get("/tech-analysis/", summary="Run technical analysis on a symbol", tags=["Stock"])
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
