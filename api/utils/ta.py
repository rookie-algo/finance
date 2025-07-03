import yfinance as yf
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


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

def compute_local_supports(df: pd.DataFrame):
    df["prev_low"] = df["Low"].shift(1)
    df["next_low"] = df["Low"].shift(-1)
    return df[(df["Low"] < df["prev_low"]) & (df["Low"] < df["next_low"])]["Low"].round(2)

def compute_local_resistances(df: pd.DataFrame):
    df["prev_high"] = df["High"].shift(1)
    df["next_high"] = df["High"].shift(-1)
    return df[(df["High"] > df["prev_high"]) & (df["High"] > df["next_high"])]["High"].round(2)

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


# === 主分析函数 ===
def full_tech_analysis(symbol: str) -> list:
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="6mo", interval="1d")
    if df.empty:
        return [f"⚠️ 无法获取 {symbol} 的数据，请检查股票代码。"], df, df

    news_df = get_news_for_symbol(ticker=ticker)

    close = df["Close"]
    df["RSI"] = compute_rsi(close)
    df["MACD"], df["MACD_SIGNAL"] = compute_macd(close)
    df["MA5"] = close.rolling(5).mean()
    df["MA10"] = close.rolling(10).mean()
    df["MA20"] = close.rolling(20).mean()
    df["BOLL_UPPER"], df["BOLL_MID"], df["BOLL_LOWER"] = compute_bollinger_bands(close)

    latest = df.dropna().iloc[-1]
    close_price = latest["Close"]
    ma5, ma10, ma20 = latest["MA5"], latest["MA10"], latest["MA20"]
    rsi, macd, signal = latest["RSI"], latest["MACD"], latest["MACD_SIGNAL"]

    supports = compute_local_supports(df)
    resistances = compute_local_resistances(df)

    analysis = [f"\n📊 {symbol} 综合技术分析", f"当前收盘价: {close_price:.2f}"]

    # === RSI
    analysis.append(f"\n🧠 RSI: {rsi:.2f}")
    if rsi < 30:
        analysis.append("💡 RSI 超卖区，可能反弹")
    elif rsi > 70:
        analysis.append("⚠️ RSI 超买区，可能回调")
    else:
        analysis.append("🔍 RSI 正常")

    # === MACD
    analysis.append(f"\n🔀 MACD: {macd:.4f} / Signal: {signal:.4f}")
    if macd > signal:
        analysis.append("📈 MACD 金叉，看涨")
    else:
        analysis.append("📉 MACD 死叉，看跌")

    # === 均线
    analysis.append(f"\n📈 均线：MA5={ma5:.2f}, MA10={ma10:.2f}, MA20={ma20:.2f}")
    if ma5 > ma10 > ma20:
        analysis.append("🟢 多头排列")
    elif ma5 < ma10 < ma20:
        analysis.append("🔴 空头排列")
    else:
        analysis.append("🟡 均线缠绕")
    if close_price > ma5 and close_price > ma10 and close_price > ma20:
        analysis.append("✅ 股价在所有均线之上，趋势强")
    elif close_price < ma5 and close_price < ma10 and close_price < ma20:
        analysis.append("⚠️ 股价低于所有均线，偏弱")
    else:
        analysis.append("⏸️ 股价在均线之间，震荡")

    # === 布林带
    analysis.append(f"\n📊 布林带：上轨={latest['BOLL_UPPER']:.2f}, 中轨={latest['BOLL_MID']:.2f}, 下轨={latest['BOLL_LOWER']:.2f}")
    if close_price > latest["BOLL_UPPER"]:
        analysis.append("📈 超出上轨，存在回调风险")
    elif close_price < latest["BOLL_LOWER"]:
        analysis.append("📉 跌破下轨，可能反弹")
    elif close_price > latest["BOLL_MID"]:
        analysis.append("🔼 中上区间，偏强")
    else:
        analysis.append("🔽 中下区间，偏弱")

    # === Fibonacci
    high_price = df["High"].max()
    low_price = df["Low"].min()
    diff = high_price - low_price
    analysis.append(f"\n📏 斐波那契回撤（高 {high_price:.2f} → 低 {low_price:.2f}）")
    for level, ratio in {
        "0.236": 0.236, "0.382": 0.382, "0.5": 0.5, "0.618": 0.618, "0.786": 0.786
    }.items():
        price = high_price - diff * ratio
        flag = "🟡 接近当前价" if abs(close_price - price) < 0.1 else ""
        analysis.append(f"Level {level}: {price:.2f} {flag}")

    # === 支撑 / 阻力
    analysis.append(f"\n📉 局部支撑位（Top 3）:")
    for p, c in supports.value_counts().head(3).items():
        analysis.append(f"🟢 {p:.2f}（{c} 次）")
    analysis.append(f"\n📈 局部阻力位（Top 3）:")
    for p, c in resistances.value_counts().head(3).items():
        analysis.append(f"🔺 {p:.2f}（{c} 次）")

    # === 策略建议
    analysis.append(f"\n📋 策略建议")
    buy_signal = (
        rsi < 30 and macd > signal and
        any(abs(close_price - lvl) < 0.1 for lvl in supports.unique())
    )
    sell_signal = (
        rsi > 70 and macd < signal and
        any(abs(close_price - lvl) < 0.1 for lvl in resistances.unique())
    )
    if buy_signal:
        analysis.append("✅ 建议：短线买入（超卖 + 金叉 + 支撑）")
    elif sell_signal:
        analysis.append("⚠️ 建议：考虑止盈（超买 + 死叉 + 阻力）")
    elif ma5 > ma10 > ma20 and macd > signal:
        analysis.append("📈 建议：持有（趋势向上）")
    elif ma5 < ma10 < ma20 and macd < signal:
        analysis.append("📉 建议：回避（趋势走弱）")
    else:
        analysis.append("⏸️ 建议：信号混杂，暂不操作")

    return analysis, df, news_df
