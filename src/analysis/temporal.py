"""Patrones temporales: por hora, día de semana, mes, día del mes."""
from __future__ import annotations
import numpy as np
import pandas as pd


def _prep(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.index = pd.to_datetime(out.index, utc=True)
    out["ret"] = np.log(out["Close"] / out["Close"].shift(1))
    out["range_pct"] = (out["High"] - out["Low"]) / out["Close"].shift(1)
    out["bullish"] = (out["Close"] > out["Open"]).astype(int)
    return out.dropna(subset=["ret"])


def by_hour(df_hourly: pd.DataFrame) -> pd.DataFrame:
    """Estadísticas de retornos por hora UTC. Requiere datos horarios."""
    d = _prep(df_hourly)
    d["hour"] = d.index.hour
    g = d.groupby("hour")["ret"]
    out = pd.DataFrame({
        "mean_bps":   g.mean() * 1e4,
        "median_bps": g.median() * 1e4,
        "std_bps":    g.std() * 1e4,
        "pct_up":     (g.apply(lambda s: (s > 0).mean())) * 100,
        "n":          g.count(),
    })
    out["t_stat"] = out["mean_bps"] / (out["std_bps"] / np.sqrt(out["n"]))
    return out.round(3)


def by_weekday(df_daily: pd.DataFrame) -> pd.DataFrame:
    d = _prep(df_daily)
    d["wd"] = d.index.day_name()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"]
    g = d.groupby("wd")["ret"]
    out = pd.DataFrame({
        "mean_bps":   g.mean() * 1e4,
        "median_bps": g.median() * 1e4,
        "std_bps":    g.std() * 1e4,
        "pct_up":     g.apply(lambda s: (s > 0).mean()) * 100,
        "n":          g.count(),
    })
    return out.reindex([d for d in order if d in out.index]).round(3)


def by_month(df_daily: pd.DataFrame) -> pd.DataFrame:
    d = _prep(df_daily)
    d["m"] = d.index.month
    g = d.groupby("m")["ret"]
    out = pd.DataFrame({
        "mean_pct":   g.sum().groupby(level=0).mean() * 100,  # aproximación: sumas log mensuales
        "std_pct":    g.std() * np.sqrt(21) * 100,
        "pct_up":     g.apply(lambda s: (s > 0).mean()) * 100,
        "n_days":     g.count(),
    })
    out.index = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"][:len(out)]
    return out.round(3)


def by_day_of_month(df_daily: pd.DataFrame) -> pd.DataFrame:
    d = _prep(df_daily)
    d["dom"] = d.index.day
    g = d.groupby("dom")["ret"]
    return pd.DataFrame({
        "mean_bps": g.mean() * 1e4,
        "pct_up":   g.apply(lambda s: (s > 0).mean()) * 100,
        "n":        g.count(),
    }).round(3)


def best_worst_hours(df_hourly: pd.DataFrame, n: int = 3) -> dict:
    h = by_hour(df_hourly).sort_values("mean_bps")
    return {
        "peores": h.head(n)[["mean_bps", "pct_up", "t_stat"]].to_dict("index"),
        "mejores": h.tail(n)[["mean_bps", "pct_up", "t_stat"]].to_dict("index"),
    }
