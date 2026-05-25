"""Diagnóstico de setup actual: combina régimen + indicadores + niveles + sesión en texto interpretable."""
from __future__ import annotations
from datetime import datetime, timezone

import pandas as pd

from src.analysis.indicators import technical_snapshot
from src.analysis.regimes import regime_summary
from src.analysis.volatility import vol_summary
from src.analysis.levels import key_levels, fibonacci_levels, psychological_levels
from src.analysis.sessions import label_session


def _bias_from_indicators(snap: dict) -> tuple[str, list[str]]:
    reasons: list[str] = []
    score = 0
    if snap["ema50_dist_pct"] > 0:
        reasons.append(f"precio sobre EMA50 (+{snap['ema50_dist_pct']:.2f}%)"); score += 1
    else:
        reasons.append(f"precio bajo EMA50 ({snap['ema50_dist_pct']:.2f}%)"); score -= 1
    if snap["ema200_dist_pct"] > 0:
        reasons.append(f"precio sobre EMA200 (+{snap['ema200_dist_pct']:.2f}%)"); score += 1
    else:
        reasons.append(f"precio bajo EMA200 ({snap['ema200_dist_pct']:.2f}%)"); score -= 1
    if snap["macd_hist"] > 0:
        reasons.append("MACD histograma positivo"); score += 1
    else:
        reasons.append("MACD histograma negativo"); score -= 1
    if snap["rsi14"] >= 70:
        reasons.append(f"RSI sobrecompra ({snap['rsi14']:.1f})"); score -= 1
    elif snap["rsi14"] <= 30:
        reasons.append(f"RSI sobreventa ({snap['rsi14']:.1f})"); score += 1
    else:
        reasons.append(f"RSI neutro ({snap['rsi14']:.1f})")

    if score >= 2:
        bias = "ALCISTA"
    elif score <= -2:
        bias = "BAJISTA"
    else:
        bias = "NEUTRO"
    return bias, reasons


def diagnose(df_daily: pd.DataFrame) -> dict:
    snap = technical_snapshot(df_daily)
    reg  = regime_summary(df_daily)
    vol  = vol_summary(df_daily)
    lvl  = key_levels(df_daily)
    fib  = fibonacci_levels(df_daily)
    psy  = psychological_levels(snap["close"])
    bias, reasons = _bias_from_indicators(snap)

    now = datetime.now(timezone.utc)
    session = label_session(now.hour)

    next_res = lvl["resistencias"][0] if lvl["resistencias"] else None
    next_sup = lvl["soportes"][0]     if lvl["soportes"]     else None

    return {
        "timestamp_utc":      now.strftime("%Y-%m-%d %H:%M"),
        "sesion_activa":      session,
        "precio":             snap["close"],
        "bias_tecnico":       bias,
        "razones_bias":       reasons,
        "regimen":            reg["regimen_actual"],
        "fase_largo_plazo":   reg["fase_largo_plazo"],
        "adx":                round(reg["adx_actual"], 1),
        "vol_anual_21d_pct":  round(vol["vol_21d_anual_actual_pct"], 2),
        "atr14_usd":          round(vol["atr_14_usd"], 2),
        "rv_percentil":       round(vol["rv_21_p_actual"] * 100, 1),
        "siguiente_resistencia": next_res,
        "siguiente_soporte":     next_sup,
        "pivots_diarios":     lvl["pivots_diarios"],
        "fib":                fib,
        "niveles_psicologicos": psy,
    }


def to_markdown(d: dict) -> str:
    lines = [
        f"## 🎯 Diagnóstico de setup — {d['timestamp_utc']} UTC",
        f"- **Precio actual:** {d['precio']:.2f}",
        f"- **Sesión activa:** {d['sesion_activa']}",
        f"- **Bias técnico:** {d['bias_tecnico']}",
        f"- **Régimen:** {d['regimen']} (ADX {d['adx']}) — fase largo plazo: {d['fase_largo_plazo']}",
        f"- **Volatilidad anual 21d:** {d['vol_anual_21d_pct']}% — ATR14 ≈ {d['atr14_usd']} USD — percentil vol: {d['rv_percentil']}%",
        "",
        "**Razones del bias:**",
    ]
    for r in d["razones_bias"]:
        lines.append(f"  - {r}")
    lines.append("")

    if d["siguiente_resistencia"]:
        r = d["siguiente_resistencia"]
        lines.append(f"- **Siguiente resistencia:** {r['level']} ({r['dist_pct']:+.2f}%) — swing del {r['date']}")
    if d["siguiente_soporte"]:
        s = d["siguiente_soporte"]
        lines.append(f"- **Siguiente soporte:** {s['level']} ({s['dist_pct']:+.2f}%) — swing del {s['date']}")

    lines.append("")
    lines.append(f"**Pivots diarios:** {d['pivots_diarios']}")
    lines.append(f"**Fibonacci ({d['fib']['direccion']}):** swing {d['fib']['swing_low']['price']} → {d['fib']['swing_high']['price']} | niveles: {d['fib']['fib']}")
    lines.append(f"**Niveles psicológicos:** arriba {d['niveles_psicologicos']['arriba']} | abajo {d['niveles_psicologicos']['abajo']}")
    return "\n".join(lines)
