#!/usr/bin/env python3
"""
Chronological parameter optimization for the VN-Index Ito Bayes-GARCH and MACD strategies.

The optimizer uses train/validation/test splits:

- train: fit GARCH and model priors
- validation: select parameters
- test: final out-of-sample evaluation only

This avoids choosing parameters directly on the final test window.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-vnindex")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from stochastic_ito_bayes_garch_strategy import (
    TRADING_DAYS,
    advanced_return_metrics,
    apply_macd_strategy,
    apply_strategy_rules,
    dataframe_to_markdown,
    finalize_long_exit_strategy,
    fit_garch,
    load_vnindex_csv,
    recursive_bayes_garch_forecast,
    sample_garch_posterior,
    trade_metrics,
)


@dataclass
class OptimizationConfig:
    data_path: Path = Path("data.csv")
    output_dir: Path = Path("outputs_optimization")
    start_date: str = "2006-01-01"
    train_ratio: float = 0.60
    valid_ratio: float = 0.20
    transaction_cost: float = 0.0005
    posterior_samples: int = 600
    random_state: int = 2026


def chronological_train_valid_test(
    df: pd.DataFrame,
    train_ratio: float,
    valid_ratio: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_end = int(len(df) * train_ratio)
    valid_end = int(len(df) * (train_ratio + valid_ratio))
    if train_end < 252 or valid_end <= train_end + 60 or len(df) <= valid_end + 60:
        raise ValueError("Not enough observations for train/validation/test optimization.")
    return df.iloc[:train_end].copy(), df.iloc[train_end:valid_end].copy(), df.iloc[valid_end:].copy()


def make_forecast_frame(
    df: pd.DataFrame,
    segment: pd.DataFrame,
    forecast: pd.DataFrame,
    split_name: str,
) -> pd.DataFrame:
    frame = segment[["date", "close", "log_return", "simple_return"]].copy().join(forecast)
    frame["split"] = split_name
    previous_close = df["close"].shift(1).reindex(frame.index)
    inferred_previous_close = frame["close"] / (1.0 + frame["simple_return"])
    frame["previous_close"] = previous_close.fillna(inferred_previous_close)
    frame["forecast_close"] = frame["previous_close"] * np.exp(frame["forecast_log_return"])
    frame["forecast_close_p05"] = frame["previous_close"] * np.exp(frame["forecast_return_p05"])
    frame["forecast_close_p95"] = frame["previous_close"] * np.exp(frame["forecast_return_p95"])
    frame["direction_actual"] = (frame["log_return"] > 0).astype(int)
    frame["direction_forecast"] = (frame["forecast_log_return"] > 0).astype(int)
    return frame


def add_backtest_price_columns(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    previous_close = out["close"].shift(1)
    inferred_previous_close = out["close"] / (1.0 + out["simple_return"])
    out["previous_close"] = previous_close.fillna(inferred_previous_close)
    return out


def evaluate_strategy_frame(frame: pd.DataFrame) -> dict[str, float]:
    metrics = advanced_return_metrics(
        frame,
        return_col="strategy_return",
        equity_col="strategy_equity",
        benchmark_col="benchmark_return",
        point_col="strategy_points",
    )
    metrics.update(trade_metrics(frame))
    metrics["exposure"] = float(frame["signal"].mean())
    metrics["entries"] = float(frame["entry"].sum())
    metrics["exits"] = float(frame["exit"].sum())
    metrics["score"] = optimization_score(metrics)
    return metrics


def optimization_score(metrics: dict[str, float]) -> float:
    sharpe = metrics.get("sharpe", np.nan)
    calmar = metrics.get("calmar", np.nan)
    cagr = metrics.get("cagr", np.nan)
    max_dd = metrics.get("max_drawdown", np.nan)
    trades = metrics.get("trades", 0.0)
    exposure = metrics.get("exposure", 0.0)

    if any(pd.isna(v) for v in [sharpe, calmar, cagr, max_dd]):
        return -1e9
    penalty = 0.0
    if trades < 5:
        penalty += 1.0
    if exposure < 0.05 or exposure > 0.95:
        penalty += 0.5
    if max_dd < -0.55:
        penalty += abs(max_dd + 0.55) * 2.0
    return float(sharpe + 0.30 * calmar + 0.20 * cagr - penalty)


def fit_forecast_block(
    df: pd.DataFrame,
    fit_df: pd.DataFrame,
    target_df: pd.DataFrame,
    drift_window: int,
    prior_strength: int,
    posterior_samples: int,
    random_state: int,
) -> pd.DataFrame:
    result = fit_garch(fit_df["log_return"])
    posterior = sample_garch_posterior(result, posterior_samples, random_state)
    prior_mean = float(fit_df["log_return"].mean())
    return recursive_bayes_garch_forecast(
        result=result,
        posterior=posterior,
        full_returns=df["log_return"],
        test_index=target_df.index,
        drift_prior_mean=prior_mean,
        drift_prior_strength=prior_strength,
        drift_window=drift_window,
        random_state=random_state + 1,
    )


def optimize_ito(
    cfg: OptimizationConfig,
    df: pd.DataFrame,
    train: pd.DataFrame,
    valid: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    drift_windows = [21, 42, 63, 126]
    prior_strengths = [63, 126, 252]
    risk_buffers = [-0.02, 0.00, 0.02, 0.04, 0.08]

    for drift_window in drift_windows:
        for prior_strength in prior_strengths:
            forecast = fit_forecast_block(
                df=df,
                fit_df=train,
                target_df=valid,
                drift_window=drift_window,
                prior_strength=prior_strength,
                posterior_samples=cfg.posterior_samples,
                random_state=cfg.random_state + drift_window + prior_strength,
            )
            valid_frame = make_forecast_frame(df, valid, forecast, "validation")
            for risk_buffer in risk_buffers:
                strategy = apply_strategy_rules(valid_frame, cfg.transaction_cost, risk_buffer)
                metrics = evaluate_strategy_frame(strategy)
                rows.append(
                    {
                        "model": "ito_bayes_garch",
                        "drift_window": drift_window,
                        "prior_strength": prior_strength,
                        "risk_buffer": risk_buffer,
                        **metrics,
                    }
                )
    return pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)


def evaluate_ito_on_test(
    cfg: OptimizationConfig,
    df: pd.DataFrame,
    fit_df: pd.DataFrame,
    test: pd.DataFrame,
    params: pd.Series,
) -> pd.DataFrame:
    forecast = fit_forecast_block(
        df=df,
        fit_df=fit_df,
        target_df=test,
        drift_window=int(params["drift_window"]),
        prior_strength=int(params["prior_strength"]),
        posterior_samples=cfg.posterior_samples,
        random_state=cfg.random_state + 99,
    )
    test_frame = make_forecast_frame(df, test, forecast, "test")
    return apply_strategy_rules(test_frame, cfg.transaction_cost, float(params["risk_buffer"]))


def optimize_macd(
    cfg: OptimizationConfig,
    train: pd.DataFrame,
    valid: pd.DataFrame,
) -> pd.DataFrame:
    history = add_backtest_price_columns(pd.concat([train, valid], axis=0).sort_index())
    rows: list[dict[str, float | int | str]] = []
    for fast in [6, 8, 10, 12, 15]:
        for slow in [18, 21, 26, 30, 35]:
            if fast >= slow:
                continue
            for signal_span in [5, 7, 9, 12]:
                full_macd = apply_macd_strategy(history, cfg.transaction_cost, fast, slow, signal_span)
                segment = full_macd.loc[valid.index].copy()
                strategy = finalize_long_exit_strategy(
                    segment,
                    segment["signal"],
                    cfg.transaction_cost,
                    signal_name=f"macd_{fast}_{slow}_{signal_span}",
                )
                metrics = evaluate_strategy_frame(strategy)
                rows.append(
                    {
                        "model": "macd",
                        "fast": fast,
                        "slow": slow,
                        "signal_span": signal_span,
                        **metrics,
                    }
                )
    return pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)


def evaluate_macd_on_test(
    cfg: OptimizationConfig,
    fit_df: pd.DataFrame,
    test: pd.DataFrame,
    params: pd.Series,
) -> pd.DataFrame:
    history = add_backtest_price_columns(pd.concat([fit_df, test], axis=0).sort_index())
    full_macd = apply_macd_strategy(
        history,
        cfg.transaction_cost,
        int(params["fast"]),
        int(params["slow"]),
        int(params["signal_span"]),
    )
    segment = full_macd.loc[test.index].copy()
    return finalize_long_exit_strategy(
        segment,
        segment["signal"],
        cfg.transaction_cost,
        signal_name=f"macd_{int(params['fast'])}_{int(params['slow'])}_{int(params['signal_span'])}",
    )


def benchmark_on_test(test: pd.DataFrame, transaction_cost: float) -> pd.DataFrame:
    frame = test[["date", "close", "log_return", "simple_return"]].copy()
    frame["split"] = "test"
    frame["previous_close"] = frame["close"] / (1.0 + frame["simple_return"])
    frame["forecast_log_return"] = 0.0
    frame["forecast_volatility"] = frame["simple_return"].rolling(63).std().fillna(frame["simple_return"].std())
    return finalize_long_exit_strategy(frame, pd.Series(1, index=frame.index), transaction_cost, "buy_hold")


def collect_comparison_rows(
    frames: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for label, frame in frames.items():
        metrics = evaluate_strategy_frame(frame)
        rows.append(
            {
                "strategy": label,
                "total_points": metrics["total_points"],
                "annual_points": metrics["annual_points"],
                "total_return": metrics["total_return"],
                "cagr": metrics["cagr"],
                "annual_volatility": metrics["annual_volatility"],
                "sharpe": metrics["sharpe"],
                "sortino": metrics["sortino"],
                "calmar": metrics["calmar"],
                "max_drawdown": metrics["max_drawdown"],
                "var_95_daily": metrics["var_95_daily"],
                "cvar_95_daily": metrics["cvar_95_daily"],
                "trades": metrics["trades"],
                "trade_win_rate": metrics["trade_win_rate"],
                "avg_trade_return": metrics["avg_trade_return"],
                "avg_trade_points": metrics["avg_trade_points"],
                "exposure": metrics["exposure"],
                "score": metrics["score"],
            }
        )
    return pd.DataFrame(rows)


def fmt_percent(value: float) -> str:
    return "" if pd.isna(value) else f"{value:.2%}"


def format_comparison(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    percent_cols = [
        "total_return",
        "cagr",
        "annual_volatility",
        "max_drawdown",
        "var_95_daily",
        "cvar_95_daily",
        "trade_win_rate",
        "avg_trade_return",
        "exposure",
    ]
    point_cols = ["total_points", "annual_points", "avg_trade_points"]
    for col in percent_cols:
        out[col] = out[col].map(fmt_percent)
    for col in point_cols:
        out[col] = out[col].map(lambda x: "" if pd.isna(x) else f"{x:,.2f}")
    for col in ["sharpe", "sortino", "calmar", "score"]:
        out[col] = out[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
    out["trades"] = out["trades"].map(lambda x: "" if pd.isna(x) else f"{x:,.0f}")
    return out


def save_equity_plot(frames: dict[str, pd.DataFrame], output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(12.5, 6))
    colors = {
        "Optimized Ito": "#047857",
        "Optimized MACD": "#ea580c",
        "Buy & Hold": "#334155",
    }
    for label, frame in frames.items():
        ax.plot(frame["date"], frame["strategy_equity"], label=label, color=colors.get(label), linewidth=1.4)
    ax.set_title("Optimized Strategies: Test Equity Curve")
    ax.set_ylabel("Growth of 1.0")
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_dir / "optimized_equity_curve_test.png", dpi=180)
    plt.close(fig)


def save_top_scores_plot(results: pd.DataFrame, title: str, path: Path) -> None:
    top = results.head(15).copy()
    labels = []
    for _, row in top.iterrows():
        if row["model"] == "ito_bayes_garch":
            labels.append(f"w{int(row['drift_window'])}/p{int(row['prior_strength'])}/b{row['risk_buffer']:.2f}")
        else:
            labels.append(f"{int(row['fast'])},{int(row['slow'])},{int(row['signal_span'])}")
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.barh(labels[::-1], top["score"].iloc[::-1], color="#2563eb")
    ax.set_title(title)
    ax.set_xlabel("Validation optimization score")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_report(
    cfg: OptimizationConfig,
    train: pd.DataFrame,
    valid: pd.DataFrame,
    test: pd.DataFrame,
    best_ito: pd.Series,
    best_macd: pd.Series,
    comparison: pd.DataFrame,
    output_dir: Path,
) -> None:
    formatted = format_comparison(comparison)
    report = f"""# Strategy Parameter Optimization Report

## Method

- Split: train / validation / test = `{cfg.train_ratio:.0%}` / `{cfg.valid_ratio:.0%}` / `{1 - cfg.train_ratio - cfg.valid_ratio:.0%}`.
- Train: `{train['date'].min().date()}` to `{train['date'].max().date()}`.
- Validation: `{valid['date'].min().date()}` to `{valid['date'].max().date()}`.
- Test: `{test['date'].min().date()}` to `{test['date'].max().date()}`.
- Selection objective: validation `Sharpe + 0.30 * Calmar + 0.20 * CAGR`, with penalties for too few trades or extreme exposure.
- Final test is not used for parameter selection.

## Best Validation Parameters

### Ito Bayes-GARCH

- `drift_window`: `{int(best_ito['drift_window'])}`
- `prior_strength`: `{int(best_ito['prior_strength'])}`
- `risk_buffer`: `{best_ito['risk_buffer']:.4f}`
- validation score: `{best_ito['score']:.3f}`

### MACD

- `fast`: `{int(best_macd['fast'])}`
- `slow`: `{int(best_macd['slow'])}`
- `signal_span`: `{int(best_macd['signal_span'])}`
- validation score: `{best_macd['score']:.3f}`

## Final Test Comparison

{dataframe_to_markdown(formatted)}

## Interpretation

The optimized MACD configuration is selected as a trend-following rule, while the Ito Bayes-GARCH configuration is selected as a stochastic drift-volatility filter. A higher validation score does not guarantee dominance on the test set; it only formalizes the parameter search without looking at future test outcomes. The gap between validation and test performance should be read as model-selection risk.
"""
    (output_dir / "optimization_report.md").write_text(report, encoding="utf-8")


def run(cfg: OptimizationConfig) -> dict[str, object]:
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    df = load_vnindex_csv(cfg.data_path)
    df = df[df["date"] >= pd.Timestamp(cfg.start_date)].reset_index(drop=True)
    train, valid, test = chronological_train_valid_test(df, cfg.train_ratio, cfg.valid_ratio)
    fit_df = pd.concat([train, valid], axis=0).sort_index()

    ito_results = optimize_ito(cfg, df, train, valid)
    macd_results = optimize_macd(cfg, train, valid)
    best_ito = ito_results.iloc[0]
    best_macd = macd_results.iloc[0]

    optimized_ito_test = evaluate_ito_on_test(cfg, df, fit_df, test, best_ito)
    optimized_macd_test = evaluate_macd_on_test(cfg, fit_df, test, best_macd)
    baseline_ito_params = pd.Series({"drift_window": 63, "prior_strength": 126, "risk_buffer": 0.02})
    baseline_macd_params = pd.Series({"fast": 12, "slow": 26, "signal_span": 9})
    baseline_ito_test = evaluate_ito_on_test(cfg, df, fit_df, test, baseline_ito_params)
    baseline_macd_test = evaluate_macd_on_test(cfg, fit_df, test, baseline_macd_params)
    buy_hold_test = benchmark_on_test(test, cfg.transaction_cost)

    comparison = collect_comparison_rows(
        {
            "Baseline Ito": baseline_ito_test,
            "Optimized Ito": optimized_ito_test,
            "Baseline MACD": baseline_macd_test,
            "Optimized MACD": optimized_macd_test,
            "Buy & Hold": buy_hold_test,
        }
    )

    ito_results.to_csv(cfg.output_dir / "ito_validation_grid.csv", index=False)
    macd_results.to_csv(cfg.output_dir / "macd_validation_grid.csv", index=False)
    comparison.to_csv(cfg.output_dir / "optimized_test_comparison.csv", index=False)
    format_comparison(comparison).to_csv(cfg.output_dir / "optimized_test_comparison_formatted.csv", index=False)
    baseline_ito_test.to_csv(cfg.output_dir / "baseline_ito_test_backtest.csv", index=False)
    optimized_ito_test.to_csv(cfg.output_dir / "optimized_ito_test_backtest.csv", index=False)
    baseline_macd_test.to_csv(cfg.output_dir / "baseline_macd_test_backtest.csv", index=False)
    optimized_macd_test.to_csv(cfg.output_dir / "optimized_macd_test_backtest.csv", index=False)
    buy_hold_test.to_csv(cfg.output_dir / "buy_hold_test_backtest.csv", index=False)

    save_equity_plot(
        {
            "Baseline Ito": baseline_ito_test,
            "Optimized Ito": optimized_ito_test,
            "Baseline MACD": baseline_macd_test,
            "Optimized MACD": optimized_macd_test,
            "Buy & Hold": buy_hold_test,
        },
        cfg.output_dir,
    )
    save_top_scores_plot(ito_results, "Top Ito Bayes-GARCH Validation Scores", cfg.output_dir / "ito_top_validation_scores.png")
    save_top_scores_plot(macd_results, "Top MACD Validation Scores", cfg.output_dir / "macd_top_validation_scores.png")
    save_report(cfg, train, valid, test, best_ito, best_macd, comparison, cfg.output_dir)

    summary = {
        "train": [str(train["date"].min().date()), str(train["date"].max().date())],
        "validation": [str(valid["date"].min().date()), str(valid["date"].max().date())],
        "test": [str(test["date"].min().date()), str(test["date"].max().date())],
        "best_ito": {
            "drift_window": int(best_ito["drift_window"]),
            "prior_strength": int(best_ito["prior_strength"]),
            "risk_buffer": float(best_ito["risk_buffer"]),
            "validation_score": float(best_ito["score"]),
        },
        "best_macd": {
            "fast": int(best_macd["fast"]),
            "slow": int(best_macd["slow"]),
            "signal_span": int(best_macd["signal_span"]),
            "validation_score": float(best_macd["score"]),
        },
        "output_dir": str(cfg.output_dir),
    }
    (cfg.output_dir / "optimization_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def parse_args() -> OptimizationConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs_optimization"))
    parser.add_argument("--start-date", default="2006-01-01")
    parser.add_argument("--train-ratio", type=float, default=0.60)
    parser.add_argument("--valid-ratio", type=float, default=0.20)
    parser.add_argument("--transaction-cost", type=float, default=0.0005)
    parser.add_argument("--posterior-samples", type=int, default=600)
    parser.add_argument("--random-state", type=int, default=2026)
    args = parser.parse_args()
    return OptimizationConfig(
        data_path=args.data,
        output_dir=args.output_dir,
        start_date=args.start_date,
        train_ratio=args.train_ratio,
        valid_ratio=args.valid_ratio,
        transaction_cost=args.transaction_cost,
        posterior_samples=args.posterior_samples,
        random_state=args.random_state,
    )


def main() -> None:
    summary = run(parse_args())
    print("Optimization completed.")
    print(f"Output directory: {summary['output_dir']}")
    print(f"Train      : {summary['train'][0]} -> {summary['train'][1]}")
    print(f"Validation : {summary['validation'][0]} -> {summary['validation'][1]}")
    print(f"Test       : {summary['test'][0]} -> {summary['test'][1]}")
    print(f"Best Ito   : {summary['best_ito']}")
    print(f"Best MACD  : {summary['best_macd']}")


if __name__ == "__main__":
    main()
