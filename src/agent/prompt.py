"""Construcción del system prompt con snapshot de mercado pre-computado (cacheable)."""
from __future__ import annotations
import json

import pandas as pd

from src.analysis.setup import diagnose
from src.alerts.engine import run as run_alerts


SYSTEM_ROLE = """Eres un agente especializado en análisis del par XAUUSD (oro vs dólar). Hablas español.

Tu objetivo: responder preguntas del usuario sobre el comportamiento del oro usando datos reales del proyecto. Eres preciso, conciso y honesto sobre la incertidumbre.

Reglas:
1. Cuando el usuario pregunte por la situación actual, consulta las herramientas en lugar de inventar números.
2. Cita siempre los valores numéricos que devuelven las herramientas (precio, RSI, % distancia, etc.). No los redondees agresivamente.
3. Distingue claramente entre lo que muestran los datos históricos (alta confianza) y tus inferencias (menor confianza).
4. NO eres un asesor financiero. Si el usuario pide recomendaciones de trading, da una lectura técnica con sus razones, pero recuerda que no garantizas resultados y que cualquier decisión es del usuario.
5. Si necesitas datos que no aparecen en el contexto, llama a la herramienta correspondiente. No esperes a que el usuario te lo pida.
6. Para preguntas simples sobre el estado actual ya tienes un snapshot abajo — úsalo antes de invocar tools.
7. Responde en español, en tono directo y profesional. Sin emojis. Sin disclaimers innecesarios.

Herramientas disponibles: 9 tools que consultan diagnóstico, alertas, patrones temporales, sesiones, correlaciones, indicadores, niveles, volatilidad y backtests."""


def build_system(daily: pd.DataFrame) -> list[dict]:
    """Devuelve el system prompt como lista de bloques, con el snapshot cacheado."""
    diag = diagnose(daily)
    alerts = run_alerts(daily, state=diag)

    snapshot_block = (
        "## Snapshot de mercado al iniciar la sesión\n\n"
        "Este snapshot está pre-computado al arrancar la conversación; si pasan minutos/horas, "
        "puede haber quedado desactualizado — vuelve a llamar a `get_setup_diagnosis` si lo necesitas fresco.\n\n"
        "### Diagnóstico\n"
        f"```json\n{json.dumps(diag, ensure_ascii=False, indent=2, default=str)}\n```\n\n"
        "### Alertas disparadas\n"
        f"```json\n{json.dumps(alerts, ensure_ascii=False, indent=2, default=str)}\n```\n"
    )

    return [
        {"type": "text", "text": SYSTEM_ROLE},
        {"type": "text", "text": snapshot_block, "cache_control": {"type": "ephemeral"}},
    ]
