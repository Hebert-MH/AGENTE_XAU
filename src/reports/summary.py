"""Generación de reporte textual en Markdown."""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
from tabulate import tabulate

from config import REPORTS_DIR
from src.analysis.temporal import by_hour, by_weekday, by_month, best_worst_hours
from src.analysis.sessions import session_stats, session_contribution
from src.analysis.volatility import vol_summary, vol_by_hour
from src.analysis.correlations import correlation_matrix, beta_to, lead_lag
from src.analysis.regimes import regime_summary
from src.analysis.indicators import technical_snapshot
from src.analysis.setup import diagnose, to_markdown as setup_md
from src.backtest.patterns import (
    backtest_best_hour, backtest_session_long,
    backtest_trend_following, backtest_mean_reversion_rsi,
)


def _md_table(df: pd.DataFrame) -> str:
    return tabulate(df, headers="keys", tablefmt="github", floatfmt=".3f")


def build(df_daily: pd.DataFrame, df_hourly: pd.DataFrame, panel_daily: dict[str, pd.DataFrame]) -> Path:
    lines: list[str] = []
    add = lines.append

    add(f"# Reporte XAUUSD — generado {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")
    add(f"- Histórico diario: {df_daily.index.min().date()} → {df_daily.index.max().date()} ({len(df_daily)} velas)")
    add(f"- Histórico horario: {df_hourly.index.min()} → {df_hourly.index.max()} ({len(df_hourly)} velas)\n")

    add("## 1. Snapshot actual\n")
    snap = technical_snapshot(df_daily)
    add(_md_table(pd.DataFrame([snap])))

    add("\n")
    add(setup_md(diagnose(df_daily)))

    add("\n## 2. Régimen y volatilidad\n")
    add(_md_table(pd.DataFrame([regime_summary(df_daily)])))
    add("")
    add(_md_table(pd.DataFrame([vol_summary(df_daily)])))

    add("\n## 3. Patrones temporales\n")
    add("### Retornos por hora UTC (top/bottom)")
    bw = best_worst_hours(df_hourly, n=5)
    add("**Mejores horas (mayor retorno medio):**")
    add(_md_table(pd.DataFrame(bw["mejores"]).T))
    add("\n**Peores horas (menor retorno medio):**")
    add(_md_table(pd.DataFrame(bw["peores"]).T))

    add("\n### Retornos por día de la semana")
    add(_md_table(by_weekday(df_daily)))

    add("\n### Estacionalidad mensual")
    add(_md_table(by_month(df_daily)))

    add("\n## 4. Sesiones de mercado\n")
    add(_md_table(session_stats(df_hourly)))
    add("\n**Aporte medio al movimiento absoluto diario por sesión (%):**")
    add(_md_table(session_contribution(df_hourly).to_frame("aporte_pct")))

    add("\n## 5. Volatilidad horaria (True Range medio en bps)\n")
    add(_md_table(vol_by_hour(df_hourly)))

    add("\n## 6. Correlaciones macro\n")
    corr = correlation_matrix(panel_daily)
    add("### Matriz (retornos log diarios)")
    add(_md_table(corr))
    add("\n### Beta de XAUUSD vs cada activo")
    add(_md_table(beta_to(panel_daily).to_frame("beta")))
    add("\n### Lead-lag (corr de XAUUSD con shift de cada activo; negativo = base lleva)")
    add(_md_table(lead_lag(panel_daily, max_lag=3)))

    add("\n## 7. Backtests de patrones\n")
    add("### Long sólo en la hora 'mejor' histórica")
    add(_md_table(pd.DataFrame([backtest_best_hour(df_hourly)])))
    add("\n### Long sólo en la sesión de overlap Londres/NY")
    add(_md_table(pd.DataFrame([backtest_session_long(df_hourly, 'OVERLAP_LDN_NY')])))
    add("\n### Trend-following EMA50/EMA200 vs Buy & Hold")
    tf = backtest_trend_following(df_daily)
    add(_md_table(pd.DataFrame(tf).T))
    add("\n### Mean reversion con RSI")
    add(_md_table(pd.DataFrame([backtest_mean_reversion_rsi(df_daily)])))

    add("\n---\n*Datos: yfinance (GC=F como proxy de XAUUSD). Este reporte es estadístico, no es consejo financiero.*\n")

    out = REPORTS_DIR / "xauusd_report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
