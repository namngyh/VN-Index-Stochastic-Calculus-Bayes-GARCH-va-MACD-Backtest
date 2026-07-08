from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .backtester import drawdown

COLORS = {
    "Buy & Hold": "#334155",
    "MACD only": "#ea580c",
    "Ito-Bayes-GARCH only": "#047857",
    "MACD + Ito hard gate": "#0891b2",
    "MACD + volatility targeting": "#7c3aed",
    "MACD + tail-risk gate": "#dc2626",
    "MACD + full defensive exposure": "#111827",
}


def plot_equity_curves(frames: dict[str, pd.DataFrame], path) -> None:
    fig, ax = plt.subplots(figsize=(13.5, 6.5))
    for name, frame in frames.items():
        ax.plot(frame["date"], frame["strategy_equity"], label=name, color=COLORS.get(name), linewidth=1.35)
    ax.set_title("Hybrid Defensive Exposure Framework: Equity Curves")
    ax.set_ylabel("Growth of 1.0")
    ax.grid(alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_drawdown_curves(frames: dict[str, pd.DataFrame], path) -> None:
    fig, ax = plt.subplots(figsize=(13.5, 6.0))
    for name, frame in frames.items():
        ax.plot(frame["date"], drawdown(frame["strategy_equity"]), label=name, color=COLORS.get(name), linewidth=1.2)
    ax.axhline(-0.15, color="#991b1b", linestyle="--", linewidth=1.0, label="-15% constraint")
    ax.set_title("Drawdown Curves")
    ax.set_ylabel("Drawdown")
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.grid(alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_position_exposure(frames: dict[str, pd.DataFrame], path) -> None:
    fig, ax = plt.subplots(figsize=(13.5, 5.8))
    for name in ["MACD only", "MACD + volatility targeting", "MACD + tail-risk gate", "MACD + full defensive exposure"]:
        frame = frames[name]
        ax.plot(frame["date"], frame["position"], label=name, color=COLORS.get(name), linewidth=1.1)
    ax.set_title("Position / Exposure Through Time")
    ax.set_ylabel("Position size")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_risk_components(frame: pd.DataFrame, path) -> None:
    cols = ["volatility_scale", "uncertainty_penalty", "tail_risk_gate", "profit_protection_cap", "equity_protection_cap"]
    fig, ax = plt.subplots(figsize=(13.5, 6.0))
    for col in cols:
        if col in frame.columns:
            ax.plot(frame["date"], frame[col], label=col, linewidth=1.1)
    ax.set_title("Risk Allocation Components")
    ax.set_ylabel("Component value")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_regime_chart(frame: pd.DataFrame, path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(13.5, 7.0), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    axes[0].plot(frame["date"], frame["close"], color="#1f2937", linewidth=1.2)
    axes[0].set_title("VN-Index Regime Diagnostic")
    axes[0].set_ylabel("Close")
    axes[0].grid(alpha=0.25)
    codes = {name: idx for idx, name in enumerate(sorted(frame["regime"].dropna().unique()))}
    y = frame["regime"].map(codes)
    axes[1].scatter(frame["date"], y, c=y, cmap="viridis", s=8)
    axes[1].set_yticks(list(codes.values()), list(codes.keys()))
    axes[1].set_ylabel("Regime")
    axes[1].grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
