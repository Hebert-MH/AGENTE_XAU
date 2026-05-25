"""Generación de gráficos."""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import REPORTS_DIR
from src.analysis.temporal import by_hour, by_weekday
from src.analysis.sessions import session_stats
from src.analysis.volatility import vol_by_hour, realized_vol
from src.analysis.indicators import add_indicators


def _save(fig, name: str) -> Path:
    path = REPORTS_DIR / f"{name}.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_returns_by_hour(df_hourly: pd.DataFrame) -> Path:
    stats = by_hour(df_hourly)
    fig, ax = plt.subplots(figsize=(11, 4.5))
    colors = ["#2ca02c" if v > 0 else "#d62728" for v in stats["mean_bps"]]
    ax.bar(stats.index, stats["mean_bps"], color=colors)
    ax.axhline(0, color="black", lw=0.6)
    ax.set_xticks(range(24))
    ax.set_xlabel("Hora UTC")
    ax.set_ylabel("Retorno medio (bps)")
    ax.set_title("XAUUSD — retorno medio por hora UTC")
    ax.grid(axis="y", alpha=0.3)
    return _save(fig, "01_returns_by_hour")


def plot_returns_by_weekday(df_daily: pd.DataFrame) -> Path:
    stats = by_weekday(df_daily)
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ["#2ca02c" if v > 0 else "#d62728" for v in stats["mean_bps"]]
    ax.bar(stats.index, stats["mean_bps"], color=colors)
    ax.axhline(0, color="black", lw=0.6)
    ax.set_ylabel("Retorno medio (bps)")
    ax.set_title("XAUUSD — retorno medio por día de la semana")
    ax.grid(axis="y", alpha=0.3)
    return _save(fig, "02_returns_by_weekday")


def plot_volatility_by_hour(df_hourly: pd.DataFrame) -> Path:
    v = vol_by_hour(df_hourly)
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.bar(v.index, v["mean_tr_bps"], color="#1f77b4", label="Media")
    ax.plot(v.index, v["p90_tr_bps"], color="#ff7f0e", marker="o", label="P90")
    ax.set_xticks(range(24))
    ax.set_xlabel("Hora UTC")
    ax.set_ylabel("True Range (bps)")
    ax.set_title("XAUUSD — volatilidad horaria")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    return _save(fig, "03_volatility_by_hour")


def plot_session_stats(df_hourly: pd.DataFrame) -> Path:
    s = session_stats(df_hourly)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].bar(s.index, s["mean_ret_bps"], color="#1f77b4")
    axes[0].axhline(0, color="black", lw=0.6)
    axes[0].set_title("Retorno medio por sesión (bps)")
    axes[0].tick_params(axis="x", rotation=20)
    axes[1].bar(s.index, s["mean_range_bps"], color="#ff7f0e")
    axes[1].set_title("Rango medio por sesión (bps)")
    axes[1].tick_params(axis="x", rotation=20)
    for ax in axes:
        ax.grid(axis="y", alpha=0.3)
    return _save(fig, "04_session_stats")


def plot_price_with_indicators(df_daily: pd.DataFrame, last: int = 365) -> Path:
    d = add_indicators(df_daily).tail(last)
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    axes[0].plot(d.index, d["Close"], color="black", lw=1, label="Close")
    axes[0].plot(d.index, d["EMA50"], color="#1f77b4", lw=1, label="EMA50")
    axes[0].plot(d.index, d["EMA200"], color="#d62728", lw=1, label="EMA200")
    axes[0].fill_between(d.index, d["BB_LO"], d["BB_UP"], color="gray", alpha=0.15, label="BB(20,2)")
    axes[0].set_title("XAUUSD — precio con indicadores")
    axes[0].legend(loc="upper left")
    axes[0].grid(alpha=0.3)
    axes[1].plot(d.index, d["RSI14"], color="#7f7f7f")
    axes[1].axhline(70, color="red", lw=0.8, ls="--")
    axes[1].axhline(30, color="green", lw=0.8, ls="--")
    axes[1].set_ylabel("RSI(14)")
    axes[1].grid(alpha=0.3)
    return _save(fig, "05_price_indicators")


def plot_correlation_matrix(corr: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(7, 5.5))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.index)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr.index)
    for i in range(corr.shape[0]):
        for j in range(corr.shape[1]):
            ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center",
                    color="white" if abs(corr.values[i, j]) > 0.5 else "black", fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.04)
    ax.set_title("Matriz de correlaciones (retornos log diarios)")
    return _save(fig, "06_correlation_matrix")


def plot_realized_vol(df_daily: pd.DataFrame) -> Path:
    rv = realized_vol(df_daily, 21) * 100
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(rv.index, rv, color="#9467bd")
    ax.axhline(float(rv.mean()), color="black", ls="--", lw=0.8, label=f"media {rv.mean():.1f}%")
    ax.set_title("XAUUSD — volatilidad realizada anualizada (ventana 21d)")
    ax.set_ylabel("Vol anualizada (%)")
    ax.grid(alpha=0.3)
    ax.legend()
    return _save(fig, "07_realized_vol")
