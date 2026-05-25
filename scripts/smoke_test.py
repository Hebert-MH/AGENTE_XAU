"""Smoke test offline: genera OHLC sintético y corre todo el pipeline sin red."""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def make_ohlc(n: int, freq: str, seed: int, drift: float = 0.0001, vol: float = 0.008) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-01", periods=n, freq=freq, tz="UTC")
    r = rng.normal(drift, vol, n)
    # añadir patrón horario sutil si es horario
    if freq.endswith("h"):
        hour_bias = (np.sin((idx.hour - 13) / 24 * 2 * np.pi)) * 5e-4
        r = r + hour_bias
    close = 1800 * np.exp(np.cumsum(r))
    open_ = np.concatenate([[1800], close[:-1]])
    high = np.maximum(open_, close) * (1 + rng.uniform(0, vol / 2, n))
    low  = np.minimum(open_, close) * (1 - rng.uniform(0, vol / 2, n))
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": rng.integers(1000, 10000, n)}, index=idx)


def main() -> int:
    print("[smoke] generando datos sintéticos...")
    daily  = make_ohlc(1200, "1D", seed=1)
    hourly = make_ohlc(24 * 365, "1h", seed=2, vol=0.002)
    panel = {
        "XAUUSD": daily,
        "DXY":    make_ohlc(1200, "1D", seed=3, vol=0.005, drift=0.0),
        "US10Y":  make_ohlc(1200, "1D", seed=4, vol=0.02),
        "SPX":    make_ohlc(1200, "1D", seed=5, vol=0.012, drift=0.0003),
        "VIX":    make_ohlc(1200, "1D", seed=6, vol=0.04),
        "SILVER": make_ohlc(1200, "1D", seed=7, vol=0.015),
        "OIL":    make_ohlc(1200, "1D", seed=8, vol=0.02),
    }

    print("[smoke] análisis temporal...")
    from src.analysis.temporal import by_hour, by_weekday, by_month
    print(f"  by_hour shape: {by_hour(hourly).shape}")
    print(f"  by_weekday shape: {by_weekday(daily).shape}")
    print(f"  by_month shape: {by_month(daily).shape}")

    print("[smoke] sesiones...")
    from src.analysis.sessions import session_stats, session_contribution
    print(session_stats(hourly))
    print("aporte_pct:\n", session_contribution(hourly))

    print("[smoke] volatilidad...")
    from src.analysis.volatility import vol_summary, vol_by_hour
    print(vol_summary(daily))
    print(f"  vol_by_hour shape: {vol_by_hour(hourly).shape}")

    print("[smoke] correlaciones...")
    from src.analysis.correlations import correlation_matrix, beta_to, lead_lag
    print(correlation_matrix(panel))
    print("beta:\n", beta_to(panel))
    print("lead_lag:\n", lead_lag(panel, max_lag=2))

    print("[smoke] regímenes...")
    from src.analysis.regimes import regime_summary
    print(regime_summary(daily))

    print("[smoke] indicadores...")
    from src.analysis.indicators import technical_snapshot
    print(technical_snapshot(daily))

    print("[smoke] niveles + diagnóstico setup...")
    from src.analysis.levels import key_levels, fibonacci_levels, psychological_levels
    print("key_levels:", key_levels(daily))
    print("fib:", fibonacci_levels(daily))
    print("psy:", psychological_levels(float(daily['Close'].iloc[-1])))
    from src.analysis.setup import diagnose, to_markdown
    print(to_markdown(diagnose(daily)))

    print("[smoke] backtests...")
    from src.backtest.patterns import (
        backtest_best_hour, backtest_session_long,
        backtest_trend_following, backtest_mean_reversion_rsi,
    )
    print("best_hour:", backtest_best_hour(hourly))
    print("session_overlap:", backtest_session_long(hourly, "OVERLAP_LDN_NY"))
    print("trend_following:", backtest_trend_following(daily))
    print("rsi_meanrev:", backtest_mean_reversion_rsi(daily))

    print("[smoke] gráficos + reporte...")
    from src.reports import plots, summary
    plots.plot_returns_by_hour(hourly)
    plots.plot_returns_by_weekday(daily)
    plots.plot_volatility_by_hour(hourly)
    plots.plot_session_stats(hourly)
    plots.plot_price_with_indicators(daily)
    plots.plot_realized_vol(daily)
    plots.plot_correlation_matrix(correlation_matrix(panel))
    out = summary.build(daily, hourly, panel)
    print(f"\n✓ Reporte: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
