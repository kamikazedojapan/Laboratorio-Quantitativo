"""Indicadores causais. NaN reinicia o warm-up; nenhum preenchimento futuro."""
import numpy as np
import pandas as pd
from numbers import Real


def _check(n):
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("Período deve ser inteiro positivo")


def sma(s, n=20):
    _check(n)
    return s.astype(float).rolling(n, min_periods=n).mean()


def smooth(s, n, alpha):
    _check(n)
    out = np.full(len(s), np.nan)
    window = []
    value = None
    for i, x in enumerate(s):
        if not np.isfinite(x):
            window, value = [], None
            continue
        if value is None:
            window.append(float(x))
            if len(window) == n:
                value = sum(window) / n
        else:
            value += alpha * (x - value)
        if value is not None:
            out[i] = value
    return pd.Series(out, index=s.index)


def ema(s, n=9):
    _check(n)
    return smooth(s, n, 2 / (n + 1))


def rsi(s, n=14):
    _check(n)
    delta = s.diff()
    gain = smooth(delta.clip(lower=0), n, 1 / n)
    loss = smooth(-delta.clip(upper=0), n, 1 / n)
    result = 100 * gain / (gain + loss)
    return result.mask((gain == 0) & (loss == 0), 50)


def bollinger(s, n=20, k=2.0):
    if isinstance(k, (bool, np.bool_)) or not isinstance(k, Real) or not np.isfinite(k) or k <= 0:
        raise ValueError("Multiplicador inválido")
    mid = sma(s, n)
    std = s.rolling(n, min_periods=n).std(ddof=0)
    return pd.DataFrame({"bb_middle": mid, "bb_upper": mid + k * std, "bb_lower": mid - k * std})


def macd(s, fast=12, slow=26, signal=9):
    for period in (fast, slow, signal):
        _check(period)
    if fast >= slow:
        raise ValueError("MACD exige fast < slow")
    line = ema(s, fast) - ema(s, slow)
    sig = ema(line, signal)
    return pd.DataFrame({"macd": line, "macd_signal": sig, "macd_histogram": line - sig})


def all_indicators(s):
    return pd.concat([pd.DataFrame({"sma20": sma(s), "ema9": ema(s, 9), "ema21": ema(s, 21), "rsi14": rsi(s)}), bollinger(s), macd(s)], axis=1)
