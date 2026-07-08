#!/usr/bin/env python3
"""
Backtest Ito Bayes-GARCH, MACD, and Buy & Hold during the most volatile VN-Index years.

The script identifies stress years from benchmark VN-Index returns, then resets
capital at the beginning of each selected year and measures all three strategies
inside those windows.
"""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-vnindex")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from stochastic_ito_bayes_garch_strategy import (
    TRADING_DAYS,
    dataframe_to_markdown,
    drawdown_stats,
)


STRATEGIES = ["Ito Bayes-GARCH", "MACD(6,26,12)", "Buy & Hold"]
STRATEGY_COLORS = {
    "Ito Bayes-GARCH": "#047857",
    "MACD(6,26,12)": "#ea580c",
    "Buy & Hold": "#334155",
}


def max_drawdown(equity: pd.Series) -> float:
    return float((equity / equity.cummax() - 1.0).min())


def compounded_return(returns: pd.Series) -> float:
    return float((1.0 + returns.fillna(0.0)).prod() - 1.0)


def load_backtests(base_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    ito = pd.read_csv(base_dir / "full_data_backtest.csv", parse_dates=["date"])
    macd = pd.read_csv(base_dir / "macd_full_data_backtest.csv", parse_dates=["date"])
    return ito, macd


def rank_stress_years(ito: pd.DataFrame, min_sessions: int = 120) -> pd.DataFrame:
    rows: list[dict[str, float | int]] = []
    data = ito.copy()
    data["year"] = data["date"].dt.year
    for year, group in data.groupby("year"):
        if len(group) < min_sessions:
            continue
        returns = group["benchmark_return"].fillna(0.0)
        equity = (1.0 + returns).cumprod()
        downside = returns[returns < 0.0]
        rows.append(
            {
                "year": int(year),
                "sessions": int(len(group)),
                "benchmark_return": compounded_return(returns),
                "annual_volatility": float(returns.std(ddof=1) * math.sqrt(TRADING_DAYS)),
                "downside_volatility": float(downside.std(ddof=1) * math.sqrt(TRADING_DAYS)) if len(downside) > 1 else 0.0,
                "max_drawdown": max_drawdown(equity),
                "worst_day": float(returns.min()),
                "best_day": float(returns.max()),
            }
        )

    ranking = pd.DataFrame(rows)
    ranking["rank_volatility"] = ranking["annual_volatility"].rank(ascending=False, method="min")
    ranking["rank_downside_vol"] = ranking["downside_volatility"].rank(ascending=False, method="min")
    ranking["rank_drawdown"] = ranking["max_drawdown"].abs().rank(ascending=False, method="min")
    ranking["rank_bad_return"] = ranking["benchmark_return"].rank(ascending=True, method="min")
    ranking["stress_score"] = (
        ranking["rank_volatility"]
        + ranking["rank_downside_vol"]
        + ranking["rank_drawdown"]
        + ranking["rank_bad_return"]
    )
    return ranking.sort_values(["stress_score", "year"]).reset_index(drop=True)


def yearly_strategy_frame(
    source: pd.DataFrame,
    year: int,
    strategy_return_col: str,
    strategy_points_col: str,
) -> pd.DataFrame:
    frame = source[source["date"].dt.year == year].copy()
    frame["strategy_return"] = frame[strategy_return_col].fillna(0.0)
    frame["strategy_points"] = frame[strategy_points_col].fillna(0.0)
    frame["strategy_equity"] = (1.0 + frame["strategy_return"]).cumprod()
    frame["strategy_cumulative_points"] = frame["strategy_points"].cumsum()
    frame["drawdown"] = frame["strategy_equity"] / frame["strategy_equity"].cummax() - 1.0
    return frame


def summarize_strategy(frame: pd.DataFrame, year: int, strategy: str) -> dict[str, float | int | str]:
    returns = frame["strategy_return"].fillna(0.0)
    equity = frame["strategy_equity"]
    downside = returns[returns < 0.0]
    dd = drawdown_stats(equity)
    trades = float(frame["entry"].sum()) if "entry" in frame.columns else np.nan
    exits = float(frame["exit"].sum()) if "exit" in frame.columns else np.nan
    exposure = float(frame["signal"].mean()) if "signal" in frame.columns else 1.0
    total_return = float(equity.iloc[-1] - 1.0)
    annual_vol = float(returns.std(ddof=1) * math.sqrt(TRADING_DAYS))
    sharpe = float(returns.mean() / returns.std(ddof=1) * math.sqrt(TRADING_DAYS)) if returns.std(ddof=1) > 0 else np.nan
    sortino = (
        float(returns.mean() / downside.std(ddof=1) * math.sqrt(TRADING_DAYS))
        if len(downside) > 1 and downside.std(ddof=1) > 0
        else np.nan
    )
    return {
        "year": year,
        "strategy": strategy,
        "sessions": int(len(frame)),
        "start_date": frame["date"].iloc[0].date().isoformat(),
        "end_date": frame["date"].iloc[-1].date().isoformat(),
        "total_return": total_return,
        "total_points": float(frame["strategy_points"].sum()),
        "annual_volatility": annual_vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": float(dd["max_drawdown"]),
        "avg_drawdown": float(dd["avg_drawdown"]),
        "ulcer_index": float(dd["ulcer_index"]),
        "var_95_daily": float(returns.quantile(0.05)),
        "cvar_95_daily": float(returns[returns <= returns.quantile(0.05)].mean()),
        "worst_day": float(returns.min()),
        "best_day": float(returns.max()),
        "win_rate": float((returns > 0.0).mean()),
        "exposure": exposure,
        "trades": trades,
        "exits": exits,
    }


def build_stress_backtests(
    ito: pd.DataFrame,
    macd: pd.DataFrame,
    stress_years: list[int],
) -> tuple[pd.DataFrame, dict[tuple[int, str], pd.DataFrame]]:
    rows: list[dict[str, float | int | str]] = []
    frames: dict[tuple[int, str], pd.DataFrame] = {}
    for year in stress_years:
        ito_frame = yearly_strategy_frame(ito, year, "strategy_return", "strategy_points")
        macd_frame = yearly_strategy_frame(macd, year, "strategy_return", "strategy_points")
        bh_frame = yearly_strategy_frame(ito, year, "benchmark_return", "benchmark_points")
        bh_frame["signal"] = 1
        bh_frame["entry"] = 0
        if not bh_frame.empty:
            bh_frame.loc[bh_frame.index[0], "entry"] = 1
        bh_frame["exit"] = 0
        for strategy, frame in [
            ("Ito Bayes-GARCH", ito_frame),
            ("MACD(6,26,12)", macd_frame),
            ("Buy & Hold", bh_frame),
        ]:
            frames[(year, strategy)] = frame
            rows.append(summarize_strategy(frame, year, strategy))
    return pd.DataFrame(rows), frames


def format_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    out = metrics.copy()
    pct_cols = [
        "total_return",
        "annual_volatility",
        "sharpe",
        "sortino",
        "max_drawdown",
        "avg_drawdown",
        "ulcer_index",
        "var_95_daily",
        "cvar_95_daily",
        "worst_day",
        "best_day",
        "win_rate",
        "exposure",
    ]
    for col in pct_cols:
        if col not in out.columns:
            continue
        if col in ["sharpe", "sortino"]:
            out[col] = out[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
        else:
            out[col] = out[col].map(lambda x: "" if pd.isna(x) else f"{x:.2%}")
    if "total_points" in out.columns:
        out["total_points"] = out["total_points"].map(lambda x: f"{x:,.2f}")
    if "trades" in out.columns:
        out["trades"] = out["trades"].map(lambda x: "" if pd.isna(x) else f"{x:,.0f}")
    if "exits" in out.columns:
        out["exits"] = out["exits"].map(lambda x: "" if pd.isna(x) else f"{x:,.0f}")
    return out


def plot_equity_curves(frames: dict[tuple[int, str], pd.DataFrame], years: list[int], output_dir: Path) -> None:
    fig, axes = plt.subplots(len(years), 1, figsize=(13, 3.1 * len(years)), sharex=False)
    if len(years) == 1:
        axes = [axes]
    for ax, year in zip(axes, years):
        for strategy in STRATEGIES:
            frame = frames[(year, strategy)]
            ax.plot(frame["date"], frame["strategy_equity"], label=strategy, color=STRATEGY_COLORS[strategy], linewidth=1.4)
        ax.set_title(f"{year}: Stress-Year Equity Curve, Capital Reset to 1.0")
        ax.set_ylabel("Equity")
        ax.grid(alpha=0.25)
        ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_dir / "stress_year_equity_curves.png", dpi=180)
    plt.close(fig)


def plot_drawdowns(frames: dict[tuple[int, str], pd.DataFrame], years: list[int], output_dir: Path) -> None:
    fig, axes = plt.subplots(len(years), 1, figsize=(13, 3.1 * len(years)), sharex=False)
    if len(years) == 1:
        axes = [axes]
    for ax, year in zip(axes, years):
        for strategy in STRATEGIES:
            frame = frames[(year, strategy)]
            ax.plot(frame["date"], frame["drawdown"], label=strategy, color=STRATEGY_COLORS[strategy], linewidth=1.4)
        ax.set_title(f"{year}: Stress-Year Drawdown")
        ax.set_ylabel("Drawdown")
        ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
        ax.grid(alpha=0.25)
        ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_dir / "stress_year_drawdowns.png", dpi=180)
    plt.close(fig)


def plot_heatmap(metrics: pd.DataFrame, years: list[int], output_dir: Path) -> None:
    selected = metrics[metrics["year"].isin(years)].copy()
    score_metrics = ["total_return", "annual_volatility", "max_drawdown", "sharpe", "total_points"]
    fig, axes = plt.subplots(1, len(score_metrics), figsize=(18, 5.5), sharey=True)
    for ax, metric in zip(axes, score_metrics):
        pivot = selected.pivot(index="strategy", columns="year", values=metric).loc[STRATEGIES]
        im = ax.imshow(pivot.to_numpy(), aspect="auto", cmap="RdYlGn")
        ax.set_title(metric)
        ax.set_xticks(range(len(pivot.columns)), pivot.columns)
        ax.set_yticks(range(len(pivot.index)), pivot.index)
        for i in range(pivot.shape[0]):
            for j in range(pivot.shape[1]):
                value = pivot.iloc[i, j]
                text = f"{value:.1%}" if metric != "total_points" else f"{value:.0f}"
                ax.text(j, i, text, ha="center", va="center", fontsize=8)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("Stress-Year Metrics Heatmap", y=1.02, fontsize=14)
    fig.tight_layout()
    fig.savefig(output_dir / "stress_year_metric_heatmap.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_year_ranking(ranking: pd.DataFrame, selected_years: list[int], output_dir: Path) -> None:
    top = ranking.head(10).copy()
    colors = ["#dc2626" if year in selected_years else "#64748b" for year in top["year"]]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.bar(top["year"].astype(str), top["stress_score"], color=colors)
    ax.set_title("Most Difficult VN-Index Years by Composite Stress Score")
    ax.set_ylabel("Lower score = more stressful")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "stress_year_ranking.png", dpi=180)
    plt.close(fig)


def short_commentary(metrics: pd.DataFrame, years: list[int]) -> list[str]:
    comments: list[str] = []
    for year in years:
        subset = metrics[metrics["year"] == year].set_index("strategy")
        best_return = subset["total_return"].idxmax()
        lowest_dd = subset["max_drawdown"].idxmax()
        best_sharpe = subset["sharpe"].idxmax()
        comments.append(
            f"- `{year}`: return tốt nhất là `{best_return}` ({subset.loc[best_return, 'total_return']:.2%}); "
            f"drawdown thấp nhất là `{lowest_dd}` ({subset.loc[lowest_dd, 'max_drawdown']:.2%}); "
            f"Sharpe tốt nhất là `{best_sharpe}` ({subset.loc[best_sharpe, 'sharpe']:.3f})."
        )
    return comments


def save_report(ranking: pd.DataFrame, metrics: pd.DataFrame, years: list[int], output_dir: Path) -> None:
    ranking_cols = ["year", "sessions", "benchmark_return", "annual_volatility", "max_drawdown", "worst_day", "stress_score"]
    ranking_fmt = ranking[ranking_cols].head(10).copy()
    for col in ["benchmark_return", "annual_volatility", "max_drawdown", "worst_day"]:
        ranking_fmt[col] = ranking_fmt[col].map(lambda x: f"{x:.2%}")
    ranking_fmt["stress_score"] = ranking_fmt["stress_score"].map(lambda x: f"{x:.0f}")

    metrics_cols = [
        "year",
        "strategy",
        "total_points",
        "total_return",
        "annual_volatility",
        "sharpe",
        "max_drawdown",
        "var_95_daily",
        "cvar_95_daily",
        "win_rate",
        "exposure",
        "trades",
    ]
    metrics_fmt = format_metrics(metrics[metrics_cols])
    comments = "\n".join(short_commentary(metrics, years))

    report = f"""# Báo Cáo Stress-Year Backtest

## Phương Pháp Chọn Năm

Các năm stress được chọn từ chuỗi VN-Index benchmark return bằng composite score:

- annualized volatility cao,
- downside volatility cao,
- max drawdown sâu,
- annual return yếu.

Mỗi năm được backtest độc lập với capital reset về `1.0` ở đầu năm. Các năm được chọn: `{', '.join(map(str, years))}`.

## Xếp Hạng Năm Stress

{dataframe_to_markdown(ranking_fmt)}

## Backtest 3 Chiến Lược Trong Các Năm Stress

{dataframe_to_markdown(metrics_fmt)}

## Đọc Nhanh Theo Từng Năm

{comments}

## Nhận Xét Tổng Quát

- Ito Bayes-GARCH là bộ lọc phòng thủ dựa trên volatility và drift. Mô hình giảm exposure rất mạnh trong năm giảm sâu, nhờ đó kiểm soát drawdown tốt, nhưng dễ bỏ lỡ pha hồi phục nhanh.
- MACD(6,26,12) phản ứng tốt hơn với trend và momentum. Vì vậy MACD thường vượt trội ở các năm có hồi phục rõ hoặc xu hướng tăng mạnh sau cú sốc.
- Buy & Hold thắng khi cả năm có xu hướng tăng rất mạnh, nhưng chịu toàn bộ drawdown và tail risk trong giai đoạn bán tháo.
- Kết quả stress-test gợi ý hướng phát triển hợp lý là dùng MACD để xác nhận xu hướng, còn Ito Bayes-GARCH làm lớp quản trị rủi ro, điều chỉnh exposure hoặc position sizing.
"""
    (output_dir / "stress_year_report.md").write_text(report, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-dir", type=Path, default=Path("outputs_stochastic_calculus"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs_stress_years"))
    parser.add_argument("--top-years", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    ito, macd = load_backtests(args.base_dir)
    ranking = rank_stress_years(ito)
    stress_years = ranking.head(args.top_years)["year"].astype(int).tolist()
    metrics, frames = build_stress_backtests(ito, macd, stress_years)

    ranking.to_csv(args.output_dir / "stress_year_ranking.csv", index=False)
    metrics.to_csv(args.output_dir / "stress_year_metrics.csv", index=False)
    format_metrics(metrics).to_csv(args.output_dir / "stress_year_metrics_formatted.csv", index=False)

    plot_year_ranking(ranking, stress_years, args.output_dir)
    plot_equity_curves(frames, stress_years, args.output_dir)
    plot_drawdowns(frames, stress_years, args.output_dir)
    plot_heatmap(metrics, stress_years, args.output_dir)
    save_report(ranking, metrics, stress_years, args.output_dir)

    print("Stress-year backtest completed.")
    print(f"Output directory: {args.output_dir}")
    print(f"Selected years: {', '.join(map(str, stress_years))}")


if __name__ == "__main__":
    main()
