# AGENTE_XAU — Análisis estadístico avanzado de XAUUSD

Agente que estudia cómo se comporta el oro (XAUUSD) usando datos históricos: en qué horas/sesiones/días tiende a subir o bajar, qué tan volátil es en cada franja, cómo se correlaciona con el dólar (DXY), bonos (US10Y), bolsa (SPX), VIX, plata y petróleo, en qué régimen está el mercado, e indicadores técnicos. Incluye backtests para validar si los patrones aguantan en sample.

> Fuente de datos: `yfinance`. `GC=F` (futuro continuo del oro CME) se usa como proxy de XAUUSD spot — es la forma estándar de tener datos públicos consistentes sin API key.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
# pipeline completo: descarga -> análisis -> gráficos -> reporte markdown
python scripts/run_analysis.py

# refrescar caché (re-descargar)
python scripts/run_analysis.py --refresh

# sólo reporte (sin gráficos, más rápido)
python scripts/run_analysis.py --no-plots

# diagnóstico rápido del setup actual (sólo consola)
python scripts/diagnose.py

# evaluar catálogo de alertas y guardar histórico
python scripts/check_alerts.py
python scripts/check_alerts.py --json

# agente LLM conversacional (requiere ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY='sk-ant-...'
python scripts/chat.py
```

## Agente LLM

`scripts/chat.py` arranca un CLI conversacional con Claude Opus 4.7:
- Pre-carga datos + snapshot del mercado en el system prompt (cacheado con `cache_control: ephemeral`)
- Adaptive thinking + `effort: "high"` para razonamiento agentico
- Expone 9 herramientas (tool use) que Claude invoca bajo demanda:
  `get_setup_diagnosis`, `get_alerts`, `get_temporal_patterns`, `get_session_stats`,
  `get_correlations`, `get_technical_indicators`, `get_levels`, `get_volatility_breakdown`, `run_backtest`

Ejemplo de uso:

```
tú> ¿cómo está el oro hoy?
tú> ¿en qué horas suele subir el oro?
tú> dame backtest del trend following y compáralo con buy&hold
tú> ¿qué setup tiene más probabilidad: long o short?
```

Salida: `reports/output/xauusd_report.md` + PNGs.

## Estructura

```
src/
├── data/loader.py            # descarga + caché parquet, retries
├── analysis/
│   ├── temporal.py           # patrones hora / día semana / mes / día mes
│   ├── sessions.py           # Asia / Londres / NY / overlap LDN-NY
│   ├── volatility.py         # ATR, vol realizada, vol por hora, regímenes
│   ├── correlations.py       # matriz, rolling, lead-lag, beta
│   ├── regimes.py            # ADX, trend/range, bull/bear (EMA cross)
│   ├── indicators.py         # RSI, MACD, Bollinger, EMAs
│   ├── levels.py             # swings, pivots, fibonacci, niveles psicológicos
│   └── setup.py              # diagnóstico textual combinando todo
├── alerts/
│   ├── rules.py              # 10 reglas declarativas (catálogo)
│   └── engine.py             # motor de evaluación + persistencia JSONL
├── agent/
│   ├── tools.py              # 9 herramientas para Claude (tool use)
│   ├── prompt.py             # system prompt + snapshot cacheable
│   └── chat.py               # loop conversacional
├── backtest/patterns.py      # backtest de patrones detectados
└── reports/
    ├── plots.py              # 7 figuras PNG (matplotlib)
    └── summary.py            # reporte markdown con tablas
config.py                     # tickers, sesiones UTC, paths
scripts/run_analysis.py       # entry-point
```

## Qué responde el agente

- ¿En qué horas UTC sube/baja el oro en media? ¿Es significativo (t-stat)?
- ¿Qué sesión mueve más el precio (Asia / Londres / overlap / NY)?
- ¿Qué días de la semana son alcistas/bajistas?
- ¿Cómo se distribuye la volatilidad a lo largo del día?
- ¿Cuál es la correlación con DXY, US10Y, SPX, VIX, plata, petróleo?
- ¿Quién lleva a quién? (lead-lag en t-1..t+3 días)
- ¿En qué régimen está el mercado ahora? (trending vs ranging, bull vs bear)
- ¿RSI/MACD/Bollinger/EMAs cómo están?
- ¿Funcionarían patrones simples (mejor hora / sesión / trend-following / mean reversion RSI)?

## Aviso

Reporte estadístico-descriptivo. No es consejo financiero. Los backtests no incluyen comisiones, slippage ni ejecución realista — sólo sirven para validar si un patrón estadístico es robusto.
