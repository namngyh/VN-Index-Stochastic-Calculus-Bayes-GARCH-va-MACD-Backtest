#!/usr/bin/env python3
"""Run the VN-Index MACD + Ito-Bayes-GARCH defensive exposure experiment."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-vnindex")

import pandas as pd
import yaml

from stochastic_ito_bayes_garch_strategy import dataframe_to_markdown
from src.backtester import backtest_position
from src.data_loader import chronological_split_labels, load_price_data
from src.indicators import add_macd_features, add_realized_risk_features
from src.ito_bayes_garch import ItoForecastConfig, walk_forward_yearly_forecasts
from src.metrics import (
    format_table,
    regime_performance,
    strategy_comparison,
    stress_period_performance,
    year_by_year_performance,
)
from src.plots import (
    plot_drawdown_curves,
    plot_equity_curves,
    plot_position_exposure,
    plot_regime_chart,
    plot_risk_components,
)
from src.risk_governor import classify_regime, compute_risk_components
from src.strategies import build_strategy_positions


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def build_feature_frame(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    full_df = load_price_data(cfg["data"]["data_path"])
    start_date = pd.Timestamp(cfg["data"]["start_date"])
    macd_full = add_macd_features(
        full_df,
        fast=int(cfg["macd"]["fast"]),
        slow=int(cfg["macd"]["slow"]),
        signal_span=int(cfg["macd"]["signal"]),
    )
    macd_full = add_realized_risk_features(
        macd_full,
        realized_window=int(cfg["risk_governor"]["realized_volatility_window"]),
        trend_window=int(cfg["risk_governor"]["trend_window"]),
    )
    forecast_cfg = ItoForecastConfig(
        drift_window=int(cfg["ito_bayes_garch"]["drift_window"]),
        prior_strength=int(cfg["ito_bayes_garch"]["prior_strength"]),
        posterior_samples=int(cfg["ito_bayes_garch"]["posterior_samples"]),
        random_state=int(cfg["ito_bayes_garch"]["random_state"]),
        min_train_observations=int(cfg["data"].get("min_train_observations", 252)),
    )
    forecasts = walk_forward_yearly_forecasts(macd_full, start_date, forecast_cfg)
    target = macd_full.loc[forecasts.index].copy().join(forecasts)
    target["previous_close"] = target["close"].shift(1).fillna(target["close"] / (1.0 + target["simple_return"]))
    target["split"] = chronological_split_labels(
        target,
        train_ratio=float(cfg["experiment"]["train_ratio"]),
        valid_ratio=float(cfg["experiment"]["valid_ratio"]),
    )
    return full_df, target


def make_frames(feature_frame: pd.DataFrame, cfg: dict) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    risk_cfg = dict(cfg["risk_governor"])
    risk_cfg["ito_risk_buffer"] = float(cfg["ito_bayes_garch"]["risk_buffer"])
    transaction_cost = float(cfg["backtest"]["transaction_cost"])
    components = compute_risk_components(feature_frame, risk_cfg)
    feature_frame = feature_frame.join(components)
    feature_frame["regime"] = classify_regime(feature_frame, components)

    positions, full_diag = build_strategy_positions(feature_frame, components, risk_cfg, transaction_cost)
    diagnostic_frame = feature_frame.join(full_diag)
    diagnostic_frame["full_defensive_position"] = positions["MACD + full defensive exposure"]

    frames = {}
    for name, position in positions.items():
        frame = backtest_position(diagnostic_frame, position, transaction_cost, name)
        frame["regime"] = diagnostic_frame["regime"]
        frame["split"] = diagnostic_frame["split"]
        frames[name] = frame
    return frames, diagnostic_frame


def top_stress_years(feature_frame: pd.DataFrame, configured_years: list[int], n: int = 5) -> list[int]:
    rows = []
    for year, group in feature_frame.groupby(feature_frame["date"].dt.year):
        if len(group) < 120:
            continue
        returns = group["simple_return"].fillna(0.0)
        equity = (1.0 + returns).cumprod()
        downside = returns[returns < 0]
        rows.append(
            {
                "year": int(year),
                "annual_volatility": float(returns.std(ddof=1) * math.sqrt(252)),
                "downside_volatility": float(downside.std(ddof=1) * math.sqrt(252)) if len(downside) > 1 else 0.0,
                "max_drawdown": float((equity / equity.cummax() - 1.0).min()),
                "annual_return": float(equity.iloc[-1] - 1.0),
            }
        )
    ranking = pd.DataFrame(rows)
    ranking["score"] = (
        ranking["annual_volatility"].rank(ascending=False, method="min")
        + ranking["downside_volatility"].rank(ascending=False, method="min")
        + ranking["max_drawdown"].abs().rank(ascending=False, method="min")
        + ranking["annual_return"].rank(ascending=True, method="min")
    )
    ranked = ranking.sort_values(["score", "year"])["year"].astype(int).tolist()
    combined = []
    for year in configured_years + ranked:
        if year not in combined and year in set(ranking["year"].astype(int)):
            combined.append(year)
        if len(combined) >= n:
            break
    return combined


def save_outputs(frames: dict[str, pd.DataFrame], diagnostic_frame: pd.DataFrame, cfg: dict, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    comparison = strategy_comparison(frames)
    yearly = year_by_year_performance(frames)
    stress_years = top_stress_years(diagnostic_frame, [int(x) for x in cfg["experiment"].get("stress_years", [])])
    stress = stress_period_performance(yearly, stress_years)
    full_frame = frames["MACD + full defensive exposure"]
    regime = regime_performance(full_frame)

    comparison.to_csv(output_dir / "strategy_comparison.csv", index=False)
    yearly.to_csv(output_dir / "year_by_year_performance.csv", index=False)
    stress.to_csv(output_dir / "stress_period_performance.csv", index=False)
    regime.to_csv(output_dir / "regime_performance.csv", index=False)

    trade_cols = [
        "strategy",
        "number_of_trades",
        "trade_hit_rate",
        "avg_trade_return",
        "avg_trade_points",
        "avg_holding_days",
        "turnover",
        "annual_turnover",
        "exposure_ratio",
    ]
    comparison[trade_cols].to_csv(output_dir / "trade_statistics.csv", index=False)
    diagnostic_frame.to_csv(output_dir / "risk_allocation_components.csv", index=False)
    for name, frame in frames.items():
        slug = name.lower().replace(" & ", "_").replace(" + ", "_").replace(" ", "_").replace("-", "_")
        frame.to_csv(output_dir / f"{slug}_backtest.csv", index=False)

    plot_equity_curves(frames, output_dir / "equity_curves.png")
    plot_drawdown_curves(frames, output_dir / "drawdown_curves.png")
    plot_position_exposure(frames, output_dir / "position_exposure.png")
    plot_risk_components(full_frame, output_dir / "risk_allocation_components.png")
    plot_regime_chart(full_frame, output_dir / "regime_chart.png")

    report = build_report(comparison, yearly, stress, regime, stress_years, cfg)
    (output_dir / "hybrid_model_report.md").write_text(report, encoding="utf-8")
    summary = summarize_results(comparison, cfg)
    summary["stress_years"] = stress_years
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def build_report(comparison: pd.DataFrame, yearly: pd.DataFrame, stress: pd.DataFrame, regime: pd.DataFrame, stress_years: list[int], cfg: dict) -> str:
    formatted_comparison = format_table(comparison)
    compact_cols = [
        "strategy",
        "total_return",
        "cagr",
        "annualized_volatility",
        "sharpe_ratio",
        "sortino_ratio",
        "calmar_ratio",
        "max_drawdown",
        "cvar_95_daily",
        "worst_month",
        "worst_year",
        "number_of_trades",
        "exposure_ratio",
        "return_per_unit_drawdown",
    ]
    compact = formatted_comparison[[c for c in compact_cols if c in formatted_comparison.columns]]
    stress_compact = format_table(stress[[c for c in ["year", "strategy", "total_return", "calmar_ratio", "sortino_ratio", "max_drawdown", "cvar_95_daily", "exposure_ratio"] if c in stress.columns]])
    regime_compact = format_table(regime[[c for c in ["regime", "observations", "total_return", "calmar_ratio", "sortino_ratio", "max_drawdown", "exposure_ratio"] if c in regime.columns]]) if len(regime) else pd.DataFrame()

    full = comparison.set_index("strategy").loc["MACD + full defensive exposure"]
    macd = comparison.set_index("strategy").loc["MACD only"]
    dd_constraint = float(cfg["risk_governor"]["max_drawdown_constraint"])
    raw_return_gap = float(macd["total_return"] - full["total_return"])
    dd_improvement = float(full["max_drawdown"] - macd["max_drawdown"])

    return f"""# Hybrid Defensive Exposure Model Report

## Executive Summary

Mô hình đề xuất là một white-box hybrid trading framework. MACD đóng vai trò tạo tín hiệu alpha theo xu hướng, trong khi Ito-Bayes-GARCH Defensive Exposure Model đóng vai trò kiểm soát rủi ro thông qua dự báo volatility, Bayesian drift shrinkage, tail-risk-aware exposure adjustment và profit protection. Dù các tham số GARCH được ước lượng thống kê, cơ chế ra quyết định vẫn minh bạch và có thể giải thích về mặt kinh tế.

Full defensive exposure model có max drawdown `{full['max_drawdown']:.2%}` so với constraint `{dd_constraint:.2%}`. So với MACD only, hybrid hy sinh `{raw_return_gap:.2%}` total return nếu số này dương, và cải thiện drawdown `{dd_improvement:.2%}` nếu số này dương.

## Current Model Review

Baseline hiện tại cho thấy MACD có raw return mạnh hơn Ito-Bayes-GARCH standalone, nhưng Ito kiểm soát drawdown và stress-period exposure tốt hơn. Vì vậy, phiên bản này không ép Ito thành alpha generator độc lập mà chuyển nó thành risk governor.

## Why MACD Should Be The Alpha Engine

MACD trả lời câu hỏi: có directional alpha/trend signal đáng giao dịch không? Trong dữ liệu hiện tại, MACD(6,26,12) phản ứng tốt với trend recovery và giữ raw return cao hơn Ito standalone.

## Why Ito-Bayes-GARCH Should Be The Defensive Exposure Model

Ito-Bayes-GARCH không nên được xem là một standalone alpha generator. Đóng góp chính của nó là cải thiện robustness của một chiến lược alpha có hướng bằng cách kiểm soát exposure dưới điều kiện stochastic volatility và Bayesian tail-risk uncertainty.

## Hybrid Model Architecture

Công thức lõi:

`position_t = MACD_signal_t * risk_allocation_t`

Full defensive exposure model:

`position_t = MACD_signal_t * volatility_scale_t * uncertainty_penalty_t * profit_protection_t`

và hard exit:

`if forecast_return_p05_t < loss_floor: position_t = 0`

Uncertainty proxy dùng trong bản này là độ rộng predictive interval chuẩn hóa: `(forecast_p95 - forecast_p05) / (3.29 * forecast_volatility) - 1`, sau đó clip về không nếu interval không rộng bất thường. Regime detection là report-only diagnostic, chưa trực tiếp điều khiển position.

## Strategy Variants

- Buy & Hold.
- MACD only.
- Ito-Bayes-GARCH only.
- MACD + Ito hard gate.
- MACD + volatility targeting.
- MACD + tail-risk gate.
- MACD + full defensive exposure model.

## Backtest Methodology

- VN-Index only.
- Long/cash only, no short-selling.
- Transaction cost: `{float(cfg['backtest']['transaction_cost']):.2%}` per position change.
- Walk-forward yearly Ito-Bayes-GARCH forecast: mỗi năm chỉ fit bằng dữ liệu trước năm đó.
- MACD signal được shift 1 phiên để tránh look-ahead bias.
- Fractional position nằm trong `[0, 1]`.

## Performance Comparison

{dataframe_to_markdown(compact)}

## Risk-Adjusted Performance

Calmar, Sortino, CVaR, time-under-water và return per unit drawdown là trọng tâm chính. Objective nghiên cứu không phải raw return đơn thuần mà là cân bằng giữa lợi nhuận, drawdown và turnover.

## Stress-Test Analysis

Stress years used: `{', '.join(map(str, stress_years))}`.

{dataframe_to_markdown(stress_compact) if len(stress_compact) else 'No stress table.'}

## Regime Analysis

{dataframe_to_markdown(regime_compact) if len(regime_compact) else 'Regime table is empty.'}

## Drawdown and Tail-Risk Analysis

Hybrid model dùng volatility targeting để giảm exposure mềm khi forecast volatility cao, tail-risk gate để exit cứng khi predictive p05 thấp hơn loss floor, uncertainty penalty để giảm vốn khi predictive interval rộng bất thường, và equity/profit protection để bảo vệ đường vốn khi drawdown hoặc volatility xấu đi.

## Interpretation

Nếu hybrid giảm max drawdown và cải thiện Calmar/Sortino so với MACD only, Ito-Bayes-GARCH layer đang tạo giá trị như một risk governor. Nếu hybrid làm mất quá nhiều return mà không cải thiện risk-adjusted metrics, risk governor đang quá bảo thủ hoặc target volatility/loss floor cần chỉnh lại trên validation.

## Limitations

- GARCH posterior vẫn là asymptotic approximation quanh MLE, chưa phải MCMC đầy đủ.
- Profit protection là path-dependent risk rule, cần stress-test thêm với phí và slippage.
- Regime detection hiện chỉ để giải thích, chưa tối ưu hoặc điều khiển position.
- Dữ liệu chỉ VN-Index, chưa mở rộng sang tài sản khác.

## Next Development Steps

1. Tối ưu target volatility, loss floor và uncertainty penalty trên validation, giữ test cuối độc lập.
2. Thử walk-forward refit theo quý hoặc tháng nếu laptop cho phép.
3. Kiểm định độ nhạy transaction cost.
4. Thử regime detection làm overlay nhẹ sau khi report-only diagnostic ổn định.
"""


def summarize_results(comparison: pd.DataFrame, cfg: dict) -> dict:
    by = comparison.set_index("strategy")
    full_name = "MACD + full defensive exposure"
    return {
        "highest_total_return": str(comparison.loc[comparison["total_return"].idxmax(), "strategy"]),
        "best_max_drawdown": str(comparison.loc[comparison["max_drawdown"].idxmax(), "strategy"]),
        "best_calmar": str(comparison.loc[comparison["calmar_ratio"].idxmax(), "strategy"]),
        "best_sortino": str(comparison.loc[comparison["sortino_ratio"].idxmax(), "strategy"]),
        "full_defensive_total_return": float(by.loc[full_name, "total_return"]),
        "full_defensive_max_drawdown": float(by.loc[full_name, "max_drawdown"]),
        "full_defensive_calmar": float(by.loc[full_name, "calmar_ratio"]),
        "full_defensive_sortino": float(by.loc[full_name, "sortino_ratio"]),
        "macd_total_return": float(by.loc["MACD only", "total_return"]),
        "macd_max_drawdown": float(by.loc["MACD only", "max_drawdown"]),
        "max_drawdown_constraint": float(cfg["risk_governor"]["max_drawdown_constraint"]),
        "full_defensive_meets_drawdown_constraint": bool(by.loc[full_name, "max_drawdown"] >= float(cfg["risk_governor"]["max_drawdown_constraint"])),
        "output_dir": str(cfg["experiment"]["output_dir"]),
    }


def run(config_path: Path) -> dict:
    cfg = load_config(config_path)
    output_dir = Path(cfg["experiment"]["output_dir"])
    _, feature_frame = build_feature_frame(cfg)
    frames, diagnostic_frame = make_frames(feature_frame, cfg)
    return save_outputs(frames, diagnostic_frame, cfg, output_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    return parser.parse_args()


def main() -> None:
    summary = run(parse_args().config)
    print("Hybrid defensive exposure experiment completed.")
    print(f"Output directory: {summary['output_dir']}")
    print(f"Highest total return: {summary['highest_total_return']}")
    print(f"Best max drawdown: {summary['best_max_drawdown']}")
    print(f"Best Calmar: {summary['best_calmar']}")
    print(f"Best Sortino: {summary['best_sortino']}")
    print(f"Full defensive max drawdown: {summary['full_defensive_max_drawdown']:.2%}")
    print(f"Meets -15% drawdown constraint: {summary['full_defensive_meets_drawdown_constraint']}")


if __name__ == "__main__":
    main()
