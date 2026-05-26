"""Herramientas que Claude puede invocar para consultar los análisis del proyecto."""
from __future__ import annotations
import json
from typing import Any

import pandas as pd

from src.analysis.temporal import by_hour, by_weekday, by_month, best_worst_hours
from src.analysis.sessions import session_stats, session_contribution
from src.analysis.volatility import vol_summary, vol_by_hour
from src.analysis.correlations import correlation_matrix, beta_to, lead_lag
from src.analysis.regimes import regime_summary
from src.analysis.indicators import technical_snapshot
from src.analysis.levels import key_levels, fibonacci_levels
from src.analysis.setup import diagnose
from src.alerts.engine import run as run_alerts
from src.backtest.patterns import (
    backtest_best_hour, backtest_session_long,
    backtest_trend_following, backtest_mean_reversion_rsi,
)


TOOL_SCHEMAS: list[dict] = [
    {
        "name": "get_setup_diagnosis",
        "description": "Devuelve el diagnóstico completo del setup actual de XAUUSD: precio, bias técnico, régimen, volatilidad, soporte/resistencia más cercanos, pivots, fibonacci y niveles psicológicos. Úsalo cuando el usuario pregunte por la situación actual del mercado.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_alerts",
        "description": "Evalúa el catálogo de 10 reglas de alerta sobre el estado actual y devuelve las disparadas, ordenadas por severidad (STRONG/WARN/INFO). Úsalo cuando el usuario pregunte por señales, oportunidades o riesgos.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_temporal_patterns",
        "description": "Estadísticas históricas de retornos por franja temporal. Útil para responder 'cuándo sube/baja el oro'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "timeframe": {
                    "type": "string",
                    "enum": ["hour", "weekday", "month"],
                    "description": "hour=hora UTC (horario), weekday=día de semana (diario), month=mes del año (diario)",
                },
                "top_n": {"type": "integer", "description": "Número de top/bottom a devolver (sólo para hour). Default 5.", "default": 5},
            },
            "required": ["timeframe"],
        },
    },
    {
        "name": "get_session_stats",
        "description": "Estadísticas por sesión de mercado: Asia, Londres, NY, overlap Londres-NY. Incluye retorno medio, volatilidad y % de aporte al movimiento diario.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_correlations",
        "description": "Correlaciones de XAUUSD con DXY, US10Y, SPX, VIX, plata, petróleo. Incluye matriz, beta y lead-lag (qué activo lleva a cuál).",
        "input_schema": {
            "type": "object",
            "properties": {
                "include_leadlag": {"type": "boolean", "description": "Incluir tabla de lead-lag (±3 días). Default true.", "default": True},
            },
            "required": [],
        },
    },
    {
        "name": "get_technical_indicators",
        "description": "Snapshot de indicadores técnicos actuales: RSI(14), distancia a EMA20/50/200, MACD histograma, posición Bollinger.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_levels",
        "description": "Niveles clave actuales: top 5 soportes/resistencias por proximidad, pivots diarios, fibonacci del último swing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "n": {"type": "integer", "description": "Número de soportes/resistencias a devolver. Default 5.", "default": 5},
            },
            "required": [],
        },
    },
    {
        "name": "get_volatility_breakdown",
        "description": "Volatilidad detallada: resumen (vol anualizada 21d, ATR, percentil) + tabla de True Range medio por hora UTC.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "run_backtest",
        "description": "Ejecuta un backtest histórico de un patrón conocido sobre los datos cacheados y devuelve métricas (retorno total, win rate, Sharpe, max drawdown).",
        "input_schema": {
            "type": "object",
            "properties": {
                "strategy": {
                    "type": "string",
                    "enum": ["best_hour", "overlap_session", "trend_following", "rsi_mean_reversion"],
                    "description": "best_hour=long en la mejor hora histórica; overlap_session=long en sesión overlap LDN-NY; trend_following=EMA50/200 cross; rsi_mean_reversion=long en RSI<30, exit RSI>=50",
                },
            },
            "required": ["strategy"],
        },
    },
]


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, pd.DataFrame):
        return obj.reset_index().to_dict("records")
    if isinstance(obj, pd.Series):
        return obj.to_dict()
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(x) for x in obj]
    if hasattr(obj, "item"):
        try:
            return obj.item()
        except (ValueError, TypeError):
            pass
    return obj


def execute(name: str, args: dict, *, daily: pd.DataFrame, hourly: pd.DataFrame, panel: dict[str, pd.DataFrame]) -> str:
    """Ejecuta una tool por nombre y devuelve JSON serializado."""
    try:
        if name == "get_setup_diagnosis":
            out = diagnose(daily)
        elif name == "get_alerts":
            out = run_alerts(daily)
        elif name == "get_temporal_patterns":
            tf = args["timeframe"]
            if tf == "hour":
                n = int(args.get("top_n", 5))
                out = best_worst_hours(hourly, n=n)
            elif tf == "weekday":
                out = by_weekday(daily)
            elif tf == "month":
                out = by_month(daily)
            else:
                return json.dumps({"error": f"timeframe desconocido: {tf}"})
        elif name == "get_session_stats":
            out = {
                "stats": session_stats(hourly),
                "aporte_pct_movimiento_diario": session_contribution(hourly).to_dict(),
            }
        elif name == "get_correlations":
            out = {"matrix": correlation_matrix(panel), "beta_xauusd_vs": beta_to(panel).to_dict()}
            if args.get("include_leadlag", True):
                out["lead_lag"] = lead_lag(panel, max_lag=3)
        elif name == "get_technical_indicators":
            out = {"snapshot": technical_snapshot(daily), "regime": regime_summary(daily)}
        elif name == "get_levels":
            n = int(args.get("n", 5))
            out = {"key_levels": key_levels(daily, n_levels=n), "fibonacci": fibonacci_levels(daily)}
        elif name == "get_volatility_breakdown":
            out = {"summary": vol_summary(daily), "by_hour_utc": vol_by_hour(hourly)}
        elif name == "run_backtest":
            strategy = args["strategy"]
            if strategy == "best_hour":
                out = backtest_best_hour(hourly)
            elif strategy == "overlap_session":
                out = backtest_session_long(hourly, "OVERLAP_LDN_NY")
            elif strategy == "trend_following":
                out = backtest_trend_following(daily)
            elif strategy == "rsi_mean_reversion":
                out = backtest_mean_reversion_rsi(daily)
            else:
                return json.dumps({"error": f"strategy desconocida: {strategy}"})
        else:
            return json.dumps({"error": f"tool desconocida: {name}"})

        return json.dumps(_json_safe(out), ensure_ascii=False, default=str)
    except Exception as exc:
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"})
