"""Definición declarativa de reglas de alerta sobre el diagnóstico de setup."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable


Severity = str  # "INFO" | "WARN" | "STRONG"


@dataclass
class Rule:
    name: str
    description: str
    severity: Severity
    condition: Callable[[dict], bool]
    message: Callable[[dict], str] = field(default=lambda d: "")
    tags: list[str] = field(default_factory=list)

    def evaluate(self, state: dict) -> dict | None:
        try:
            if self.condition(state):
                return {
                    "name":        self.name,
                    "severity":    self.severity,
                    "description": self.description,
                    "message":     self.message(state) if self.message else "",
                    "tags":        self.tags,
                }
        except (KeyError, TypeError, ValueError):
            return None
        return None


def _close_to(price: float, level: float, tol_pct: float = 0.3) -> bool:
    return abs(price - level) / price * 100 <= tol_pct


def _next_res_dist(s: dict) -> float | None:
    r = s.get("siguiente_resistencia")
    return r["dist_pct"] if r else None


def _next_sup_dist(s: dict) -> float | None:
    sup = s.get("siguiente_soporte")
    return sup["dist_pct"] if sup else None


CATALOG: list[Rule] = [
    Rule(
        name="RSI_OVERSOLD_NEAR_SUPPORT",
        description="RSI sobreventa con soporte cercano - potencial rebote",
        severity="STRONG",
        tags=["mean-reversion", "long"],
        condition=lambda s: (
            s["bias_tecnico"] != "ALCISTA"
            and any("RSI sobreventa" in r for r in s["razones_bias"])
            and (_next_sup_dist(s) is not None and abs(_next_sup_dist(s)) <= 0.5)
        ),
        message=lambda s: f"RSI sobreventa con soporte a {_next_sup_dist(s):+.2f}% - vigilar reversion",
    ),
    Rule(
        name="RSI_OVERBOUGHT_NEAR_RESISTANCE",
        description="RSI sobrecompra con resistencia cercana - potencial rechazo",
        severity="STRONG",
        tags=["mean-reversion", "short"],
        condition=lambda s: (
            any("sobrecompra" in r for r in s["razones_bias"])
            and (_next_res_dist(s) is not None and _next_res_dist(s) <= 0.5)
        ),
        message=lambda s: f"RSI sobrecompra con resistencia a {_next_res_dist(s):+.2f}% - vigilar rechazo",
    ),
    Rule(
        name="TREND_CONTINUATION_NY",
        description="Trend alcista fuerte en sesion NY (la mas productiva historicamente)",
        severity="STRONG",
        tags=["trend", "long", "NY"],
        condition=lambda s: (
            s["regimen"] == "TREND_UP"
            and s["fase_largo_plazo"] == "BULL"
            and s["sesion_activa"] in ("NY", "OVERLAP_LDN_NY")
            and s["adx"] >= 25
        ),
        message=lambda s: f"Trend alcista en {s['sesion_activa']} con ADX {s['adx']} - momentum favorable",
    ),
    Rule(
        name="VOLATILITY_EXTREME",
        description="Volatilidad realizada en percentil alto - riesgo elevado",
        severity="WARN",
        tags=["risk", "volatility"],
        condition=lambda s: s["rv_percentil"] >= 85,
        message=lambda s: f"Vol anual 21d {s['vol_anual_21d_pct']}% (percentil {s['rv_percentil']}%) - reducir tamano",
    ),
    Rule(
        name="VOLATILITY_COMPRESSION",
        description="Volatilidad en percentil bajo - posible expansion inminente",
        severity="INFO",
        tags=["volatility", "breakout"],
        condition=lambda s: s["rv_percentil"] <= 20,
        message=lambda s: f"Vol anual 21d {s['vol_anual_21d_pct']}% (percentil {s['rv_percentil']}%) - vigilar breakout",
    ),
    Rule(
        name="NEAR_PSYCHOLOGICAL_LEVEL",
        description="Precio cerca de un nivel psicologico (multiplo de 50)",
        severity="INFO",
        tags=["levels"],
        condition=lambda s: any(
            _close_to(s["precio"], lvl, 0.2)
            for lvl in (s["niveles_psicologicos"]["arriba"] + s["niveles_psicologicos"]["abajo"])
        ),
        message=lambda s: f"Precio {s['precio']:.2f} cerca de nivel psicologico",
    ),
    Rule(
        name="RANGE_BOUND",
        description="Mercado en rango - favorecer estrategias de reversion",
        severity="INFO",
        tags=["regime"],
        condition=lambda s: s["regimen"] == "RANGE" and s["adx"] < 18,
        message=lambda s: f"RANGE con ADX {s['adx']} - operar extremos del rango",
    ),
    Rule(
        name="BIAS_DIVERGES_FROM_LONGTERM",
        description="Bias tecnico contradice la fase de largo plazo - posible swing temporal",
        severity="WARN",
        tags=["divergencia"],
        condition=lambda s: (
            (s["bias_tecnico"] == "BAJISTA" and s["fase_largo_plazo"] == "BULL")
            or (s["bias_tecnico"] == "ALCISTA" and s["fase_largo_plazo"] == "BEAR")
        ),
        message=lambda s: f"Bias {s['bias_tecnico']} en fase {s['fase_largo_plazo']} - posible pullback",
    ),
    Rule(
        name="PRICE_AT_FIB_618",
        description="Precio en zona de retroceso 61.8% - nivel clave",
        severity="STRONG",
        tags=["fibonacci"],
        condition=lambda s: _close_to(s["precio"], s["fib"]["fib"]["61.8%"], 0.3),
        message=lambda s: f"Precio en Fib 61.8% ({s['fib']['fib']['61.8%']}) - zona de decision",
    ),
    Rule(
        name="NY_SESSION_ACTIVE",
        description="Sesion NY activa - historicamente la de mayor retorno medio",
        severity="INFO",
        tags=["session"],
        condition=lambda s: s["sesion_activa"] == "NY",
        message=lambda s: "Sesion NY activa - ventana historica de mayor movimiento",
    ),
]
