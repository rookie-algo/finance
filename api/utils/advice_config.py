
rules = [
  {
    "name": "趋势上行，继续持有",
    "condition": "ma5 > ma10 and ma10 > ma20 and macd > macd_signal and adx > 25",
    "action": "继续持有",
    "reason": "短中期均线多头排列，MACD 金叉，ADX 显示强趋势"
  },
  {
    "name": "短期涨幅过大，建议减仓",
    "condition": "rsi > 68 and cci > 100 and max(volumn_resistances + local_resistances) - Close < 5",
    "action": "考虑部分止盈",
    "reason": "RSI 超买，CCI 过热，接近压力位"
  },
  {
    "name": "突破布林上轨，动能过强",
    "condition": "Close > boll_upper and rsi > 70",
    "action": "观察或减仓",
    "reason": "价格突破布林带上轨，短期可能回调"
  },
  {
    "name": "接近支撑位，考虑低吸",
    "condition": "Close < ma20 and Close - min(local_supports + volumn_supports) < 5",
    "action": "逢低加仓",
    "reason": "价格接近支撑区域，可考虑低吸"
  },
  {
    "name": "高波动且无方向，建议观望",
    "condition": "atr / Close > 0.03 and adx < 20",
    "action": "暂时观望",
    "reason": "当前波动大且缺乏明确方向"
  },
  {
    "name": "MACD 死叉，趋势减弱",
    "condition": "macd < macd_signal and adx < 20",
    "action": "观察或减仓",
    "reason": "MACD 死叉且趋势强度低，短期可能回调"
  },
  {
    "name": "CCI 超买",
    "condition": "cci > 100 and rsi > 65",
    "action": "减仓",
    "reason": "CCI 和 RSI 同时处于超买区域"
  },
  {
    "name": "CCI 超卖，短期反弹可能",
    "condition": "cci < -100 and rsi < 35",
    "action": "关注反弹机会",
    "reason": "CCI 超卖，可能触底反弹"
  },
  {
    "name": "接近斐波那契关键位",
    "condition": "abs(Close - fibonacci['0.382']) < 3 or abs(Close - fibonacci['0.618']) < 3",
    "action": "重点关注",
    "reason": "价格接近斐波那契关键位置，可能反转"
  },
  {
    "name": "接近历史压力，建议止盈",
    "condition": "resistance and resistance[0] - Close < 3 and pnl_pct > 10",
    "action": "止盈",
    "reason": "价格接近历史压力位，建议锁定收益"
  },
  {
    "name": "回调跌破支撑，考虑止损",
    "condition": "support and Close < support[0] and pnl_pct < -8",
    "action": "止损",
    "reason": "价格跌破关键支撑位，亏损扩大，建议止损"
  },
  {
    "name": "OBV 背离，注意动能转弱",
    "condition": "macd > macd_signal and obv < obv_prev",
    "action": "警惕虚假上涨",
    "reason": "MACD 向上但 OBV 下降，动能背离"
  },
  {
    "name": "短期震荡，等待突破",
    "condition": "abs(ma5 - ma20) / ma20 < 0.01 and adx < 20",
    "action": "保持观望",
    "reason": "价格在均线附近震荡，暂无方向信号"
  }
]


risk_map = {
    "止损": "⚠️ 高风险提示",
    "减仓": "⚠️ 盈利回撤风险",
    "止盈": "✅ 盈利保护",
    "逢低加仓": "🟡 技术反弹机会",
    "试探性加仓": "🟡 技术反弹机会",
    "继续持有": "🟢 趋势良好",
    "考虑部分止盈": "🟢 趋势上涨中的风控",
    "观察或减仓": "🟡 中性偏空",
    "警惕虚假上涨": "⚠️ 风险提示",
    "暂时观望": "🟡 等待趋势明确",
    "保持观望": "🟡 无操作建议",
    "重点关注": "🔍 关键位置观察",
    "关注反弹机会": "🟡 反弹可能",
    "观察": "🟡 中性",
}