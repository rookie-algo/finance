import os
import requests

from openai import OpenAI


client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API")
)


def generate_prompt_from_api_response(data: dict) -> str:
    tech = data["tech_analysis_indicators"]
    advice = data["advices"]["advices"][0].replace("\n", "\n  ")
    news_items = data.get("News", [])

    # 合并斐波那契回撤
    fibo = tech.get("fibonacci", {})
    fibo_text = ", ".join([f"{k}={round(v, 2)}" for k, v in fibo.items()])

    # 新闻摘要
    news_summary = "\n".join([
        f"- {item['title']}（情绪评分：{item.get('Sentiment', 0):.2f}）"
        for item in news_items[:5]
    ])

    return f"""据以下信息对股票 {data['Symbol']} 给出操作建议和分析，并指出可能的风险或机会。

当前股价：${data['Close']:.2f}（昨日收盘：${data['PrevClose']:.2f}，涨跌幅：{data['ChangePct']}%）

📊 技术指标：
- RSI：{tech['rsi']:.2f}
- MACD：{tech['macd']:.2f}，MACD Signal：{tech['macd_signal']:.2f}
- ADX：{tech['adx']:.2f}
- CCI：{tech['cci']:.2f}
- ATR：{tech['atr']:.2f}
- 均线：MA5={tech['ma5']:.2f}，MA10={tech['ma10']:.2f}，MA20={tech['ma20']:.2f}
- 布林带：上轨={tech['boll_upper']:.2f}，中轨={tech['boll_mid']:.2f}，下轨={tech['boll_lower']:.2f}
- OBV：{tech['obv']}
- 斐波那契回撤位：{fibo_text}
- 局部支撑位：{tech['local_supports']}
- 成交量支撑位：{tech['volumn_supports']}
- 局部压力位：{tech['local_resistances']}
- 成交量压力位：{tech['volumn_resistances']}

📌 当前系统建议：
  {advice}

📰 最近相关新闻摘要（自动分析情绪）：
{news_summary}

请你结合以上信息，回答以下内容：
1. 对该股票的操作建议（持有、加仓、减仓、止盈/止损等）
2. 给出建议的理由，结合技术面和新闻情绪
3. 指出风险点或机会点
4. 并用中文输出
"""



def request_to_groq(prompt: str, model: str = "llama3-70b-8192") -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是一名经验丰富的证券分析师，擅长结合技术指标和新闻情绪做出投资建议"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content