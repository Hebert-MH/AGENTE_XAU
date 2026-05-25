"""Análisis por sesión de mercado (Asia / Londres / NY / overlap)."""
from __future__ import annotations
import numpy as np
import pandas as pd

from config import SESSIONS_UTC


def label_session(hour: int) -> str:
    if SESSIONS_UTC["OVERLAP_LDN_NY"][0] <= hour < SESSIONS_UTC["OVERLAP_LDN_NY"][1]:
        return "OVERLAP_LDN_NY"
    if SESSIONS_UTC["NY"][0] <= hour < SESSIONS_UTC["NY"][1]:
        return "NY"
    if SESSIONS_UTC["LONDON"][0] <= hour < SESSIONS_UTC["LONDON"][1]:
        return "LONDON"
    return "ASIA"


def session_stats(df_hourly: pd.DataFrame) -> pd.DataFrame:
    d = df_hourly.copy()
    d.index = pd.to_datetime(d.index, utc=True)
    d["ret"] = np.log(d["Close"] / d["Close"].shift(1))
    d["range"] = (d["High"] - d["Low"]) / d["Close"].shift(1)
    d["session"] = [label_session(h) for h in d.index.hour]
    d = d.dropna(subset=["ret"])

    g = d.groupby("session")
    out = pd.DataFrame({
        "mean_ret_bps":  g["ret"].mean() * 1e4,
        "std_ret_bps":   g["ret"].std() * 1e4,
        "mean_range_bps": g["range"].mean() * 1e4,
        "pct_up":        g["ret"].apply(lambda s: (s > 0).mean()) * 100,
        "n_horas":       g["ret"].count(),
    })
    order = ["ASIA", "LONDON", "OVERLAP_LDN_NY", "NY"]
    return out.reindex([s for s in order if s in out.index]).round(3)


def session_daily_pl(df_hourly: pd.DataFrame) -> pd.DataFrame:
    """Retorno acumulado por sesión y por día (qué sesión 'mueve' más cada día)."""
    d = df_hourly.copy()
    d.index = pd.to_datetime(d.index, utc=True)
    d["ret"] = np.log(d["Close"] / d["Close"].shift(1))
    d["session"] = [label_session(h) for h in d.index.hour]
    d["date"] = d.index.date
    pivot = d.dropna().groupby(["date", "session"])["ret"].sum().unstack("session").fillna(0.0)
    return (pivot * 100).round(4)  # en %


def session_contribution(df_hourly: pd.DataFrame) -> pd.Series:
    """% del movimiento diario total que aporta cada sesión (en valor absoluto)."""
    pl = session_daily_pl(df_hourly)
    abs_pl = pl.abs()
    total = abs_pl.sum(axis=1).replace(0, np.nan)
    share = abs_pl.div(total, axis=0).mean() * 100
    return share.round(2).sort_values(ascending=False)
