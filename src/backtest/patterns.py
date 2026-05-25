"""Backtests simples para validar patrones detectados (no es estrategia productiva)."""
from __future__ import annotations
import numpy as np
import pandas as pd

from src.analysis.temporal import by_hour
from src.analysis.sessions import label_session


def _stats(pnl: pd.Series) -> dict:
    pnl = pnl.dropna()
    if pnl.empty:
        return {"n": 0}
    cum = pnl.sum()
    wins = (pnl > 0).sum()
    losses = (pnl < 0).sum()
    return {
        "n":              int(len(pnl)),
        "ret_total_pct":  float(cum * 100),
        "ret_medio_bps":  float(pnl.mean() * 1e4),
        "win_rate":       float(wins / len(pnl) * 100),
        "expect_bps":     float(pnl.mean() * 1e4),
        "sharpe_anual":   float(pnl.mean() / pnl.std() * np.sqrt(252 * 6.5)) if pnl.std() else 0.0,
        "max_dd_pct":     float((pnl.cumsum() - pnl.cumsum().cummax()).min() * 100),
    }


def backtest_best_hour(df_hourly: pd.DataFrame) -> dict:
    """Long en la hora con mayor mean_ret histórico, salida 1h después."""
    stats = by_hour(df_hourly).sort_values("mean_bps", ascending=False)
    target_hour = int(stats.index[0])
    d = df_hourly.copy()
    d.index = pd.to_datetime(d.index, utc=True)
    d["ret"] = np.log(d["Close"] / d["Close"].shift(1))
    sig = (d.index.hour == target_hour)
    pnl = d["ret"].where(sig)
    return {"hora_objetivo_utc": target_hour, **_stats(pnl)}


def backtest_session_long(df_hourly: pd.DataFrame, session: str = "OVERLAP_LDN_NY") -> dict:
    d = df_hourly.copy()
    d.index = pd.to_datetime(d.index, utc=True)
    d["ret"] = np.log(d["Close"] / d["Close"].shift(1))
    sig = pd.Series([label_session(h) for h in d.index.hour], index=d.index) == session
    return {"session": session, **_stats(d["ret"].where(sig))}


def backtest_trend_following(df_daily: pd.DataFrame, fast: int = 50, slow: int = 200) -> dict:
    """Long cuando EMA(fast) > EMA(slow), flat en caso contrario."""
    c = df_daily["Close"]
    ef = c.ewm(span=fast, adjust=False).mean()
    es = c.ewm(span=slow, adjust=False).mean()
    pos = (ef > es).astype(int)
    ret = np.log(c / c.shift(1))
    pnl = (ret * pos.shift(1)).dropna()
    base = _stats(pnl)
    # buy & hold para comparar
    bh = _stats(ret)
    return {"trend_following": base, "buy_and_hold": bh}


def backtest_mean_reversion_rsi(df_daily: pd.DataFrame, low: float = 30, high: float = 70) -> dict:
    """Compra cuando RSI cruza al alza desde <30, vende al cruzar 50; corto inverso."""
    from src.analysis.indicators import rsi
    c = df_daily["Close"]
    r = rsi(c, 14)
    long_entry = (r.shift(1) < low) & (r >= low)
    exit_long  = r >= 50
    pos = pd.Series(0, index=c.index)
    state = 0
    for i in range(len(c)):
        if state == 0 and long_entry.iloc[i]:
            state = 1
        elif state == 1 and exit_long.iloc[i]:
            state = 0
        pos.iloc[i] = state
    ret = np.log(c / c.shift(1))
    pnl = (ret * pos.shift(1)).dropna()
    return _stats(pnl)
