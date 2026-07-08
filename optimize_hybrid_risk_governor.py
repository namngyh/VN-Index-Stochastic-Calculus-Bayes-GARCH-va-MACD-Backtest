#!/usr/bin/env python3
"""Optimize the hybrid MACD + Ito-Bayes-GARCH risk governor on validation only."""

from __future__ import annotations

import argparse
import itertools
import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-vnindex")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from stochastic_ito_bayes_garch_strategy import dataframe_to_markdown
from run_hybrid_experiment import build_feature_frame, make_frames, summarize_results
from src.metrics import format_table, strategy_comparison, stress_period_performance, year_by_year_performance
from src.plots import plot_drawdown_curves, plot_equity_curves, plot_position_exposure, plot_risk_components

FULL_MODEL = "MACD + full defensive exposure"
MACD_MODEL = "MACD only"
VOL_MODEL = "MACD + volatility targeting"


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def objective(metrics: dict[str, float], max_dd_constraint: float) -> float:
    cagr = metrics.get("cagr", np.nan)
    calmar = metrics.get("calmar_ratio", np.nan)
    sortino = metrics.get("sortino_ratio", np.nan)
    turnover = metrics.get("annual_turnover", np.nan)
    max_dd = metrics.get("max_drawdown", np.nan)
    exposure = metrics.get("exposure_ratio", np.nan)
    if any(pd.isna(v) for v in [cagr, calmar, sortino, turnover, max_dd, exposure]):
        return -1e9
    dd_penalty = 0.0
    if max_dd < max_dd_constraint:
        dd_penalty = abs(max_dd - max_dd_constraint) * 20.0
    exposure_penalty = 0.0
    if exposure < 0.10:
        exposure_penalty += (0.10 - exposure) * 2.0
    if exposure > 0.75:
        exposure_penalty += (exposure - 0.75) * 2.0
    turnover_penalty = 0.02 * turnover
    return float(0.40 * cagr + 0.30 * calmar + 0.20 * sortino - turnover_penalty - dd_penalty - exposure_penalty)


def parameter_grid(base_cfg: dict) -> list[dict[str, float]]:
    risk = base_cfg["risk_governor"]
    values = {
        "target_volatility": [0.12, 0.15, 0.18, 0.20, 0.25],
        "loss_floor": [-0.030, -0.025, -0.020, -0.015],
        "uncertainty_penalty_k": [0.0, 0.5, 1.0],
        "profit_lock_threshold": [0.08, 0.12],
        "warning_drawdown": [0.08, 0.10],
    }
    keys = list(values.keys())
    grid = []
    for combo in itertools.product(*(values[k] for k in keys)):
        params = dict(zip(keys, combo))
        params["danger_drawdown"] = float(risk["danger_drawdown"])
        params["uncertainty_penalty_min"] = float(risk["uncertainty_penalty_min"])
        params["uncertainty_penalty_max"] = float(risk["uncertainty_penalty_max"])
        grid.append(params)
    return grid


def cfg_with_params(base_cfg: dict, params: dict[str, float]) -> dict:
    cfg = json.loads(json.dumps(base_cfg))
    for key, value in params.items():
        cfg["risk_governor"][key] = float(value)
    return cfg


def evaluate_segment(feature_frame: pd.DataFrame, cfg: dict, split: str) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], pd.DataFrame]:
    segment = feature_frame[feature_frame["split"] == split].copy()
    frames, diagnostic = make_frames(segment, cfg)
    comparison = strategy_comparison(frames)
    return comparison, frames, diagnostic


def optimize(base_cfg: dict, feature_frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    rows = []
    max_dd_constraint = float(base_cfg["risk_governor"]["max_drawdown_constraint"])
    for params in parameter_grid(base_cfg):
        cfg = cfg_with_params(base_cfg, params)
        comparison, _, _ = evaluate_segment(feature_frame, cfg, "validation")
        full = comparison.set_index("strategy").loc[FULL_MODEL].to_dict()
        rows.append({**params, **full, "objective": objective(full, max_dd_constraint)})
    results = pd.DataFrame(rows).sort_values("objective", ascending=False).reset_index(drop=True)
    best_params = {key: float(results.iloc[0][key]) for key in ["target_volatility", "loss_floor", "uncertainty_penalty_k", "profit_lock_threshold", "warning_drawdown", "danger_drawdown", "uncertainty_penalty_min", "uncertainty_penalty_max"]}
    return results, best_params


def save_top_plot(results: pd.DataFrame, output_dir: Path) -> None:
    top = results.head(20).copy()
    labels = [
        f"tv={row.target_volatility:.2f}, lf={row.loss_floor:.3f}, k={row.uncertainty_penalty_k:.1f}, w={row.warning_drawdown:.2f}"
        for row in top.itertuples()
    ]
    fig, ax = plt.subplots(figsize=(12.5, 7.2))
    ax.barh(labels[::-1], top["objective"].iloc[::-1], color="#2563eb")
    ax.set_title("Top Hybrid Risk Governor Validation Scores")
    ax.set_xlabel("Validation objective")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "hybrid_validation_top_scores.png", dpi=180)
    plt.close(fig)


def save_report(
    base_cfg: dict,
    best_cfg: dict,
    best_params: dict[str, float],
    validation_results: pd.DataFrame,
    validation_comparison: pd.DataFrame,
    test_comparison: pd.DataFrame,
    full_comparison: pd.DataFrame,
    output_dir: Path,
) -> None:
    best = validation_results.iloc[0]
    formatted_validation = format_table(validation_comparison)
    formatted_test = format_table(test_comparison)
    formatted_full = format_table(full_comparison)
    full_test = test_comparison.set_index("strategy").loc[FULL_MODEL]
    macd_test = test_comparison.set_index("strategy").loc[MACD_MODEL]
    vol_test = test_comparison.set_index("strategy").loc[VOL_MODEL]
    report = f"""# Hybrid Risk Governor Optimization Report

## Method

- Alpha engine fixed: `MACD({base_cfg['macd']['fast']},{base_cfg['macd']['slow']},{base_cfg['macd']['signal']})`.
- Ito-Bayes-GARCH role: defensive risk governor / capital allocation engine.
- Search set: target volatility, tail-risk loss floor, uncertainty penalty, profit lock threshold and warning drawdown.
- Selection split: validation only.
- Final test is not used for parameter selection.
- Objective: `0.40*CAGR + 0.30*Calmar + 0.20*Sortino - turnover_penalty - drawdown_constraint_penalty - exposure_penalty`.
- Max drawdown constraint: `{float(base_cfg['risk_governor']['max_drawdown_constraint']):.2%}`.

## Best Validation Parameters

| Parameter | Value |
|---|---:|
| target_volatility | {best_params['target_volatility']:.2%} |
| loss_floor | {best_params['loss_floor']:.2%} |
| uncertainty_penalty_k | {best_params['uncertainty_penalty_k']:.2f} |
| profit_lock_threshold | {best_params['profit_lock_threshold']:.2%} |
| warning_drawdown | {best_params['warning_drawdown']:.2%} |
| danger_drawdown | {best_params['danger_drawdown']:.2%} |
| validation objective | {best['objective']:.4f} |

## Validation Comparison

{dataframe_to_markdown(formatted_validation)}

## Final Test Comparison

{dataframe_to_markdown(formatted_test)}

## Full Sample Diagnostic Comparison

{dataframe_to_markdown(formatted_full)}

## Interpretation

On the final test segment, optimized full defensive exposure has total return `{full_test['total_return']:.2%}`, max drawdown `{full_test['max_drawdown']:.2%}`, Calmar `{full_test['calmar_ratio']:.3f}` and Sortino `{full_test['sortino_ratio']:.3f}`.

MACD only on the same test segment has total return `{macd_test['total_return']:.2%}`, max drawdown `{macd_test['max_drawdown']:.2%}`, Calmar `{macd_test['calmar_ratio']:.3f}` and Sortino `{macd_test['sortino_ratio']:.3f}`.

Volatility targeting has total return `{vol_test['total_return']:.2%}`, max drawdown `{vol_test['max_drawdown']:.2%}`, Calmar `{vol_test['calmar_ratio']:.3f}` and Sortino `{vol_test['sortino_ratio']:.3f}`.

If full defensive exposure satisfies the drawdown constraint but still trails MACD in Calmar/Sortino, the risk governor is useful for capital preservation but remains too conservative for return-seeking allocation. If volatility targeting has better Calmar/Sortino while missing the strict drawdown constraint, it should be treated as the balanced candidate for the next tuning round.
"""
    (output_dir / "hybrid_optimization_report.md").write_text(report, encoding="utf-8")


def run(config_path: Path) -> dict[str, object]:
    base_cfg = load_config(config_path)
    output_dir = Path("outputs_hybrid_optimization")
    output_dir.mkdir(parents=True, exist_ok=True)
    _, feature_frame = build_feature_frame(base_cfg)
    validation_results, best_params = optimize(base_cfg, feature_frame)
    best_cfg = cfg_with_params(base_cfg, best_params)

    validation_comparison, _, _ = evaluate_segment(feature_frame, best_cfg, "validation")
    test_comparison, test_frames, test_diag = evaluate_segment(feature_frame, best_cfg, "test")
    full_frames, full_diag = make_frames(feature_frame, best_cfg)
    full_comparison = strategy_comparison(full_frames)
    yearly = year_by_year_performance(full_frames)
    stress_years = [2008, 2020, 2022, 2018, 2006]
    stress = stress_period_performance(yearly, stress_years)

    validation_results.to_csv(output_dir / "hybrid_validation_grid.csv", index=False)
    format_table(validation_results.head(50)).to_csv(output_dir / "hybrid_validation_grid_top50_formatted.csv", index=False)
    validation_comparison.to_csv(output_dir / "validation_strategy_comparison.csv", index=False)
    test_comparison.to_csv(output_dir / "test_strategy_comparison.csv", index=False)
    full_comparison.to_csv(output_dir / "full_strategy_comparison.csv", index=False)
    yearly.to_csv(output_dir / "optimized_year_by_year_performance.csv", index=False)
    stress.to_csv(output_dir / "optimized_stress_period_performance.csv", index=False)
    test_diag.to_csv(output_dir / "optimized_test_risk_components.csv", index=False)
    full_diag.to_csv(output_dir / "optimized_full_risk_components.csv", index=False)
    for name, frame in test_frames.items():
        slug = name.lower().replace(" & ", "_").replace(" + ", "_").replace(" ", "_").replace("-", "_")
        frame.to_csv(output_dir / f"optimized_test_{slug}_backtest.csv", index=False)

    save_top_plot(validation_results, output_dir)
    plot_equity_curves(test_frames, output_dir / "optimized_test_equity_curves.png")
    plot_drawdown_curves(test_frames, output_dir / "optimized_test_drawdown_curves.png")
    plot_position_exposure(test_frames, output_dir / "optimized_test_position_exposure.png")
    plot_risk_components(test_frames[FULL_MODEL], output_dir / "optimized_test_risk_allocation_components.png")
    save_report(base_cfg, best_cfg, best_params, validation_results, validation_comparison, test_comparison, full_comparison, output_dir)

    summary = summarize_results(test_comparison, {**best_cfg, "experiment": {**best_cfg["experiment"], "output_dir": str(output_dir)}})
    summary["best_params"] = best_params
    summary["best_validation_objective"] = float(validation_results.iloc[0]["objective"])
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    return parser.parse_args()


def main() -> None:
    summary = run(parse_args().config)
    print("Hybrid risk governor optimization completed.")
    print(f"Output directory: {summary['output_dir']}")
    print(f"Best params: {summary['best_params']}")
    print(f"Highest total return on test: {summary['highest_total_return']}")
    print(f"Best max drawdown on test: {summary['best_max_drawdown']}")
    print(f"Best Calmar on test: {summary['best_calmar']}")
    print(f"Best Sortino on test: {summary['best_sortino']}")
    print(f"Optimized full defensive max drawdown: {summary['full_defensive_max_drawdown']:.2%}")
    print(f"Meets -15% drawdown constraint: {summary['full_defensive_meets_drawdown_constraint']}")


if __name__ == "__main__":
    main()
