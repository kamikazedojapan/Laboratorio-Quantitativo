import pandas as pd
from .indicators import all_indicators


def signals(data, strategy):
    i = all_indicators(data.Close)
    if strategy == "ema":
        spread = i.ema9 - i.ema21
        buy = (spread > 0) & (spread.shift() <= 0)
        sell = (spread < 0) & (spread.shift() >= 0)
    elif strategy == "rsi":
        buy = (i.rsi14 > 30) & (i.rsi14.shift() <= 30)
        sell = (i.rsi14 > 70) & (i.rsi14.shift() <= 70)
    elif strategy == "session_hold":
        buy, sell = pd.Series(False, index=data.index), pd.Series(False, index=data.index)
    else:
        raise ValueError("Estratégia desconhecida")
    return pd.DataFrame({"buy": buy, "sell": sell}, index=data.index), i
