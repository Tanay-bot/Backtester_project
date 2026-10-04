# btc sma crossover backtest, daily bars from the LSE api
# buy when fast sma is above slow sma, sell when it flips

from lse import LSE
import pandas as pd
from key import API_KEY

# api key lives in key.py (gitignored)
client = LSE(api_key=API_KEY)

print("fetching btc candles...")
candles = client.candles("BTC/USD", "1d", start="2024-01-01")
print("got", len(candles), "daily candles")

df = pd.DataFrame(candles)
df = df.sort_values("timestamp").reset_index(drop=True)

fast = 20
slow = 50
fee = 0.001  # 0.1% fee per trade

df["sma_fast"] = df["close"].rolling(fast).mean()
df["sma_slow"] = df["close"].rolling(slow).mean()

cash = 10000.0
coins = 0.0
last_buy_price = 0.0
wins = 0
sells = 0

equity_dates = []
equity_values = []
trades = []

print("made it to the loop")
for i in range(1, len(df)):
    # signal from previous bar, no lookahead
    # nan smas at the start -> stays flat
    if df["sma_fast"][i - 1] > df["sma_slow"][i - 1]:
        target = 1
    else:
        target = 0

    open_price = df["open"][i]

    if target == 1 and coins == 0:
        coins = (cash * (1 - fee)) / open_price
        last_buy_price = open_price
        trades.append({"date": df["timestamp"][i], "side": "BUY", "price": round(open_price, 2), "coins": round(coins, 6)})
        cash = 0.0
    elif target == 0 and coins > 0:
        cash = coins * open_price * (1 - fee)
        if open_price > last_buy_price:
            wins = wins + 1
        sells = sells + 1
        trades.append({"date": df["timestamp"][i], "side": "SELL", "price": round(open_price, 2), "cash_out": round(cash, 2)})
        coins = 0.0

    equity_dates.append(df["timestamp"][i])
    equity_values.append(cash + coins * df["close"][i])

# max drawdown
peak = 0.0
max_dd = 0.0
for v in equity_values:
    if v > peak:
        peak = v
    dd = (peak - v) / peak
    if dd > max_dd:
        max_dd = dd

days = len(df)

total_return = (equity_values[-1] / 10000.0 - 1) * 100

print("")
print("===== RESULTS =====")
print("total return:", round(total_return, 2), "%")
print("max drawdown:", round(max_dd * 100, 2), "%")
print("trades:", len(trades))
if sells > 0:
    print("win rate:", round(wins / sells * 100, 1), "% (of", sells, "sells)")
print("final equity: $", round(equity_values[-1], 2))

print("")
print("trade log:")
for t in trades:
    print(t)

# todo: sharpe, cagr, buy and hold benchmark
