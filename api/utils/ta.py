import json
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import yfinance as yf

from .advice_config import risk_map, rules


# === 仓位计算 ===
def calculate_position(sub_df):
    """根据交易记录计算持仓和投资金额"""
    buys = sub_df[sub_df["Operation"] == "BUY"]
    sells = sub_df[sub_df["Operation"] == "SELL"]
    shares = buys["Num_of_Shares"].sum() - sells["Num_of_Shares"].sum()
    invested = buys["Amount"].sum() - sells["Amount"].sum()
    return shares, invested

# === 技术指标函数 ===
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def compute_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    return macd, macd_signal

def compute_bollinger_bands(series, window=20, num_std=2):
    mid = series.rolling(window).mean()
    std = series.rolling(window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower

def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['High']
    low = df['Low']
    close = df['Close']

    plus_dm = (high - high.shift(1)).clip(lower=0)
    minus_dm = (low.shift(1) - low).clip(lower=0)

    tr1 = (high - low)
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()

    plus_di = 100 * (plus_dm.rolling(period).sum() / atr)
    minus_di = 100 * (minus_dm.rolling(period).sum() / atr)

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(period).mean()
    return adx

def compute_obv(df: pd.DataFrame) -> pd.Series:
    obv = [0]
    close = df['Close']
    volume = df['Volume']

    for i in range(1, len(df)):
        if close[i] > close[i - 1]:
            obv.append(obv[-1] + volume[i])
        elif close[i] < close[i - 1]:
            obv.append(obv[-1] - volume[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)

def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['High']
    low = df['Low']
    close = df['Close']

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def compute_cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
    tp = (df['High'] + df['Low'] + df['Close']) / 3  # Typical Price
    tp_mean = tp.rolling(window=period).mean()
    mean_dev = tp.rolling(window=period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
    cci = (tp - tp_mean) / (0.015 * mean_dev)
    return cci

def get_dynamic_bin_width(prices: List[float], percent: float = 0.01, min_width: float = 0.2) -> float:
    """
    Determine bin width as a percentage of the price range, with a minimum threshold.
    e.g., 1% of price range or at least $0.2
    """
    prices = pd.Series(prices)
    price_range = prices.max() - prices.min()
    width = max(price_range * percent, min_width)
    return round(width, 2)

def find_supports_by_clustered_range(price_list: List[float], top_n: int = 3) -> List[float]:
    """
    Cluster prices into buckets and return top N most frequent price zones as support levels.
    
    Args:
        price_list: list of float prices
        bin_width: float, e.g. 1.0 means cluster by $1 range
        top_n: number of support levels to return

    Returns:
        List of support zone center prices (float)
    """
    prices = pd.Series(price_list)
    min_price = prices.min()
    max_price = prices.max()
    bin_width = get_dynamic_bin_width(price_list)
    bins = np.arange(min_price, max_price + bin_width, bin_width)
    bucketed = pd.cut(prices, bins=bins)
    
    # Count prices in each bucket and get the centers of top N buckets
    grouped = prices.groupby(bucketed).count()
    top_zones = grouped.sort_values(ascending=False).head(top_n)

    # Compute the center price of each bin as support level
    levels = [(interval.left + interval.right) / 2 for interval in top_zones.index]
    
    return sorted(levels)

def compute_local_supports(df: pd.DataFrame):
    df["prev_low"] = df["Low"].shift(1)
    df["next_low"] = df["Low"].shift(-1)
    price_list = df[(df["Low"] < df["prev_low"]) & (df["Low"] < df["next_low"])]["Low"].round(2).astype(int).tolist()
    return find_supports_by_clustered_range(price_list)

def compute_local_resistances(df: pd.DataFrame):
    df["prev_high"] = df["High"].shift(1)
    df["next_high"] = df["High"].shift(-1)
    price_list = df[(df["High"] > df["prev_high"]) & (df["High"] > df["next_high"])]["High"].round(2).astype(int).tolist()
    return find_supports_by_clustered_range(price_list)

def compute_auto_bins(price: pd.Series, min_bin: int = 10, max_bin: int = 50, target_width: float = 1.5) -> int:
    """
    根据价格波动范围自动确定合适的 bins 数量
    - target_width: 每个价格区间大致的宽度
    - min_bin/max_bin: 限制 bins 的上下限
    """
    price_range = price.max() - price.min()
    bins = int(price_range // target_width)
    return max(min(bins, max_bin), min_bin)

def compute_volume_based_support_resistance(df: pd.DataFrame, bins: int = 10) -> Dict[str, List[float]]:
    """
    基于收盘价和成交量计算成交量密集的支撑位和压力位
    返回3个最强支撑和压力位（成交量最大），按与当前价格的接近程度排序
    """
    df = df.dropna().copy()
    price = df["Close"]
    bins = compute_auto_bins(price)

    # 分桶
    price_bins = np.linspace(price.min(), price.max(), bins + 1)
    df["price_bin"] = pd.cut(price, bins=price_bins)

    # 累计每个价格区间的成交量
    volume_by_price = df.groupby("price_bin")["Volume"].sum()

    # 计算每个区间中心价格
    bin_centers = [(b.left + b.right) / 2 for b in volume_by_price.index]
    volume_by_price.index = bin_centers

    current_price = price.iloc[-1]

    # 分成下方支撑和上方压力
    lower = volume_by_price[volume_by_price.index < current_price].sort_values(ascending=False)
    upper = volume_by_price[volume_by_price.index > current_price].sort_values(ascending=False)

    # 按与当前价的接近程度排序
    support_levels = sorted(lower.head(6).index, key=lambda x: abs(x - current_price))
    resistance_levels = sorted(upper.head(6).index, key=lambda x: abs(x - current_price))

    return {
        "support": [round(s, 2) for s in support_levels][:3],
        "resistance": [round(r, 2) for r in resistance_levels][:3]
    }


# === 抓取最新汇率 ===
def get_exchange_rate():
    ticker = yf.Ticker("EURUSD=X")
    return ticker.history(period="1d").Close.iloc[-1]

# === 抓取最新新闻 ===
def get_news_for_symbol(ticker):
    analyzer = SentimentIntensityAnalyzer()
    news_df = pd.DataFrame([news["content"] for news in ticker.news[:10]])[['contentType', 'title', 'summary', 'provider']]
    news_df['Sentiment'] = news_df.apply(lambda x: analyzer.polarity_scores(x.summary)["compound"], axis=1)
    return news_df

# === 抓取最新评级 ===
def get_upgrade_downgrate(ticker):
    return pd.DataFrame(ticker.recommendations.head().to_dict(orient='records'))[["strongBuy", "buy", "hold", "sell", "strongSell"]].to_dict(orient="records")

# === 主分析函数 ===
def full_tech_analysis(symbol: str) -> list:
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="6mo", interval="1d")
    if df.empty:
        return [f"⚠️ 无法获取 {symbol} 的数据，请检查股票代码。"], df, df

    news_df = get_news_for_symbol(ticker=ticker)

    supports = compute_local_supports(df)
    resistances = compute_local_resistances(df)
    volumn_supports_and_resistances = compute_volume_based_support_resistance(df)
    close = df["Close"]
    df["RSI"] = compute_rsi(close)
    df["MACD"], df["MACD_SIGNAL"] = compute_macd(close)
    df["MA5"] = close.rolling(5).mean()
    df["MA10"] = close.rolling(10).mean()
    df["MA20"] = close.rolling(20).mean()
    df["BOLL_UPPER"], df["BOLL_MID"], df["BOLL_LOWER"] = compute_bollinger_bands(close)
    df['ADX'] = compute_adx(df)
    df['OBV'] = compute_obv(df)
    df['ATR'] = compute_atr(df)
    df['CCI'] = compute_cci(df)
    latest = df.iloc[-1]
    close_price = latest["Close"]
    ma5, ma10, ma20 = latest["MA5"], latest["MA10"], latest["MA20"]
    rsi, macd, signal = latest["RSI"], latest["MACD"], latest["MACD_SIGNAL"]
    adx, obv, atr, cci = latest["ADX"], latest["OBV"], latest["ATR"], latest["CCI"]
    tech_analysis_indicators = {
        'close_price': close_price,
        'rsi': rsi,
        'macd': macd,
        'macd_signal': signal,
        'ma5': ma5,
        'ma10': ma10,
        'ma20': ma20,
        'symbol': symbol,
        'boll_upper': latest["BOLL_UPPER"],
        'boll_lower': latest["BOLL_LOWER"],
        'boll_mid': latest["BOLL_MID"],
        'local_supports': supports,
        'local_resistances': resistances,
        'volumn_supports': volumn_supports_and_resistances['support'],
        'volumn_resistances': volumn_supports_and_resistances['resistance'],
        'adx': adx,
        'obv': obv,
        'atr': atr,
        'cci': cci,
        'fibonacci': {}
    }
    # === Fibonacci
    high_price = df["High"].max()
    low_price = df["Low"].min()
    diff = high_price - low_price
    # analysis.append(f"\n📏 斐波那契回撤（高 {high_price:.2f} → 低 {low_price:.2f}）")
    for level, ratio in {
        "0.236": 0.236, "0.382": 0.382, "0.5": 0.5, "0.618": 0.618, "0.786": 0.786
    }.items():
        price = high_price - diff * ratio
        tech_analysis_indicators['fibonacci'][level] = price
        # analysis.append(f"Level {level}: {price:.2f} {flag}")

    return tech_analysis_indicators, df, news_df

def generate_analysis_report(tech_analysis_indicators: Dict[str, Any]):

    def evaluate_condition(context: Dict[str, Any], expression: str) -> bool:
        try:
            return eval(expression, {}, context)
        except Exception:
            return False
    reports = {
        "title": f"📊 分析对象：{tech_analysis_indicators['symbol']}\n",
        "advices": []
    }
    for rule in rules:
        if evaluate_condition(tech_analysis_indicators, rule["condition"]):
            risk = risk_map.get(rule["action"])
            if risk:
                report = (
                    f"📌 建议操作：{rule["action"]}\n"
                    f"🎯 触发规则：{rule["name"]}\n"
                    f"📈 分析理由：{rule["reason"]}\n"
                    f"🏷️ 风险等级：{risk}"
                )
                reports['advices'].append(report)
    if not reports["advices"]:
        report = (
            f"📌 建议操作：观察\n"
            f"📈 分析理由：暂无触发任何规则\n"
            f"🏷️ 风险等级：🟡 中性"
        )
        reports['advices'].append(report)
    return reports

