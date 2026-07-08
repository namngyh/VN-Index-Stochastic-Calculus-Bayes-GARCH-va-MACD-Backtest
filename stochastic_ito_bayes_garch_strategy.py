#!/usr/bin/env python3
"""
VN-Index stochastic-calculus strategy with Ito/GBM intuition and Bayes-GARCH risk.

Model idea
----------
S_t follows a discrete daily version of

    dS_t / S_t = mu_t dt + sigma_t dW_t

Ito's lemma gives the log-price dynamic

    d log(S_t) = (mu_t - 0.5 sigma_t^2) dt + sigma_t dW_t

The script estimates next-day log returns and conditional volatility, then turns
that forecast into a long/cash trading rule for VN-Index.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-vnindex")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from arch import arch_model
from scipy.stats import norm
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


TRADING_DAYS = 252


@dataclass
class StrategyConfig:
    data_path: Path = Path("data.csv")
    output_dir: Path = Path("outputs_stochastic_calculus")
    start_date: str = "2006-01-01"
    train_ratio: float = 0.70
    transaction_cost: float = 0.0005
    risk_buffer: float = 0.08
    drift_window: int = 126
    drift_prior_strength: int = 63
    macd_fast: int = 6
    macd_slow: int = 26
    macd_signal: int = 12
    posterior_samples: int = 2000
    random_state: int = 42


def _non_empty(tokens: Iterable[str]) -> list[str]:
    return [t.strip() for t in tokens if t.strip() != ""]


def _parse_price(tokens: list[str], pos: int) -> tuple[float, int]:
    """Parse one OHLC value, repairing values like '1','0.39' -> 1000.39."""
    token = tokens[pos]
    if (
        token.isdigit()
        and len(token) <= 2
        and pos + 1 < len(tokens)
        and tokens[pos + 1].replace(".", "", 1).isdigit()
        and float(tokens[pos + 1]) < 1000
    ):
        return float(token) * 1000.0 + float(tokens[pos + 1]), pos + 2
    return float(token), pos + 1


def _parse_volume(tokens: list[str], pos: int) -> float:
    pieces: list[str] = []
    for token in tokens[pos:]:
        if token.replace(".", "", 1).isdigit():
            pieces.append(token.split(".")[0])
    if not pieces:
        return np.nan
    try:
        return float("".join(pieces))
    except ValueError:
        return np.nan


def load_vnindex_csv(path: Path) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        next(handle, None)
        for line_no, line in enumerate(handle, start=2):
            tokens = _non_empty(line.rstrip("\n").split(","))
            if len(tokens) < 5:
                continue
            date_raw = tokens[0]
            values = tokens[1:]
            try:
                pos = 0
                open_, pos = _parse_price(values, pos)
                high, pos = _parse_price(values, pos)
                low, pos = _parse_price(values, pos)
                close, pos = _parse_price(values, pos)
                volume = _parse_volume(values, pos)
            except (ValueError, IndexError) as exc:
                raise ValueError(f"Cannot parse OHLC row {line_no}: {line!r}") from exc
            rows.append(
                {
                    "date": date_raw,
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                }
            )

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["date", "open", "high", "low", "close"])
    df = df.sort_values("date").drop_duplicates("date", keep="last")
    df = df[df["close"] > 0].reset_index(drop=True)
    df["log_close"] = np.log(df["close"])
    df["log_return"] = df["log_close"].diff()
    df["simple_return"] = df["close"].pct_change()
    return df.dropna(subset=["log_return"]).reset_index(drop=True)


def chronological_split(df: pd.DataFrame, train_ratio: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_idx = int(len(df) * train_ratio)
    if split_idx < 252 or len(df) - split_idx < 60:
        raise ValueError("Not enough observations for a reliable chronological train/test split.")
    return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()


def fit_garch(train_returns: pd.Series):
    returns_pct = train_returns * 100.0
    model = arch_model(
        returns_pct,
        mean="Constant",
        vol="GARCH",
        p=1,
        o=0,
        q=1,
        dist="StudentsT",
        rescale=False,
    )
    return model.fit(disp="off", show_warning=False)


def sample_garch_posterior(result, samples: int, random_state: int) -> pd.DataFrame:
    """Approximate Bayes-GARCH via the asymptotic normal posterior around MLE."""
    rng = np.random.default_rng(random_state)
    params = result.params[["mu", "omega", "alpha[1]", "beta[1]"]]
    cov = result.param_cov.loc[params.index, params.index].to_numpy()
    cov = np.nan_to_num(cov, nan=0.0, posinf=0.0, neginf=0.0)
    cov = cov + np.eye(len(params)) * 1e-10

    draws: list[np.ndarray] = []
    attempts = 0
    while len(draws) < samples and attempts < samples * 30:
        attempts += 1
        candidate = rng.multivariate_normal(params.to_numpy(), cov)
        mu, omega, alpha, beta = candidate
        if omega > 0 and alpha >= 0 and beta >= 0 and alpha + beta < 0.999:
            draws.append(candidate)

    if len(draws) < max(100, samples // 10):
        base = params.to_numpy()
        fallback = np.tile(base, (samples - len(draws), 1))
        fallback[:, 1] = np.maximum(fallback[:, 1], 1e-9)
        fallback[:, 2] = np.clip(fallback[:, 2], 1e-9, 0.35)
        fallback[:, 3] = np.clip(fallback[:, 3], 1e-9, 0.995 - fallback[:, 2])
        draws.extend(fallback)

    return pd.DataFrame(np.asarray(draws[:samples]), columns=params.index)


def recursive_bayes_garch_forecast(
    result,
    posterior: pd.DataFrame,
    full_returns: pd.Series,
    test_index: pd.Index,
    drift_prior_mean: float,
    drift_prior_strength: int,
    drift_window: int,
    random_state: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    returns_pct = full_returns * 100.0
    mu = posterior["mu"].to_numpy()
    omega = posterior["omega"].to_numpy()
    alpha = posterior["alpha[1]"].to_numpy()
    beta = posterior["beta[1]"].to_numpy()

    last_train_pos = full_returns.index.get_loc(test_index[0]) - 1
    previous_return = returns_pct.iloc[last_train_pos]
    previous_variance = float(result.conditional_volatility.iloc[-1] ** 2)
    variances = np.full(len(posterior), previous_variance)

    records: list[dict[str, float]] = []
    for idx in test_index:
        pos = full_returns.index.get_loc(idx)
        recent_returns = full_returns.iloc[max(0, pos - drift_window) : pos].dropna()
        recent_mean = float(recent_returns.mean()) if len(recent_returns) else drift_prior_mean

        variances = omega + alpha * np.square(previous_return - mu) + beta * variances
        variances = np.clip(variances, 1e-10, None)

        vol_draws = np.sqrt(variances) / 100.0
        drift_mean = (
            drift_prior_strength * drift_prior_mean + len(recent_returns) * recent_mean
        ) / (drift_prior_strength + len(recent_returns))
        drift_std = max(float(np.mean(vol_draws)) / math.sqrt(drift_prior_strength + len(recent_returns)), 1e-8)
        mean_log_return_draws = rng.normal(drift_mean, drift_std, size=len(posterior))
        brownian_shocks = rng.normal(size=len(posterior))
        predictive_draws = mean_log_return_draws + vol_draws * brownian_shocks

        records.append(
            {
                "forecast_log_return": float(np.mean(mean_log_return_draws)),
                "forecast_volatility": float(np.mean(vol_draws)),
                "forecast_return_p05": float(np.quantile(predictive_draws, 0.05)),
                "forecast_return_p50": float(np.quantile(predictive_draws, 0.50)),
                "forecast_return_p95": float(np.quantile(predictive_draws, 0.95)),
                "ito_drift_annual": float(
                    np.mean((mean_log_return_draws + 0.5 * np.square(vol_draws)) * TRADING_DAYS)
                ),
            }
        )
        previous_return = returns_pct.loc[idx]

    return pd.DataFrame(records, index=test_index)


def bayesian_rolling_drift(
    full_returns: pd.Series,
    target_index: pd.Index,
    prior_mean: float,
    prior_strength: int,
    drift_window: int,
) -> pd.Series:
    forecasts: list[float] = []
    for idx in target_index:
        pos = full_returns.index.get_loc(idx)
        recent_returns = full_returns.iloc[max(0, pos - drift_window) : pos].dropna()
        recent_mean = float(recent_returns.mean()) if len(recent_returns) else prior_mean
        forecasts.append(
            (
                prior_strength * prior_mean + len(recent_returns) * recent_mean
            )
            / (prior_strength + len(recent_returns))
        )
    return pd.Series(forecasts, index=target_index)


def in_sample_garch_forecast(
    result,
    full_returns: pd.Series,
    train: pd.DataFrame,
    drift_prior_mean: float,
    drift_prior_strength: int,
    drift_window: int,
) -> pd.DataFrame:
    fitted_return = bayesian_rolling_drift(
        full_returns=full_returns,
        target_index=train.index,
        prior_mean=drift_prior_mean,
        prior_strength=drift_prior_strength,
        drift_window=drift_window,
    )
    fitted_vol = result.conditional_volatility / 100.0
    out = pd.DataFrame(
        {
            "forecast_log_return": fitted_return,
            "forecast_volatility": fitted_vol.to_numpy(),
        },
        index=train.index,
    )
    return out


def build_prediction_table(
    df: pd.DataFrame,
    train: pd.DataFrame,
    test: pd.DataFrame,
    train_forecast: pd.DataFrame,
    test_forecast: pd.DataFrame,
    transaction_cost: float,
    risk_buffer: float,
    macd_fast: int,
    macd_slow: int,
    macd_signal: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_pred = train[["date", "close", "log_return", "simple_return"]].copy()
    train_pred = train_pred.join(train_forecast)
    train_pred["split"] = "train"

    test_pred = test[["date", "close", "log_return", "simple_return"]].copy()
    test_pred = test_pred.join(test_forecast)
    test_pred["split"] = "test"

    pred = pd.concat([train_pred, test_pred], axis=0).sort_index()
    previous_close = df["close"].shift(1).reindex(pred.index)
    inferred_previous_close = pred["close"] / (1.0 + pred["simple_return"])
    pred["previous_close"] = previous_close.fillna(inferred_previous_close)
    pred["forecast_close"] = pred["previous_close"] * np.exp(pred["forecast_log_return"])
    pred["forecast_close_p05"] = pred["previous_close"] * np.exp(
        pred.get("forecast_return_p05", pred["forecast_log_return"] - 1.64 * pred["forecast_volatility"])
    )
    pred["forecast_close_p95"] = pred["previous_close"] * np.exp(
        pred.get("forecast_return_p95", pred["forecast_log_return"] + 1.64 * pred["forecast_volatility"])
    )
    pred["direction_actual"] = (pred["log_return"] > 0).astype(int)
    pred["direction_forecast"] = (pred["forecast_log_return"] > 0).astype(int)

    full_strategy = apply_strategy_rules(pred, transaction_cost, risk_buffer)
    test_strategy = apply_strategy_rules(pred[pred["split"] == "test"].copy(), transaction_cost, risk_buffer)
    full_macd = apply_macd_strategy(pred, transaction_cost, macd_fast, macd_slow, macd_signal)
    test_macd = full_macd[full_macd["split"] == "test"].copy()
    test_macd = finalize_long_exit_strategy(test_macd, test_macd["signal"], transaction_cost)

    return pred, full_strategy, test_strategy, full_macd, test_macd


def finalize_long_exit_strategy(
    frame: pd.DataFrame,
    signal: pd.Series,
    transaction_cost: float,
    signal_name: str = "signal",
) -> pd.DataFrame:
    strategy = frame.copy()
    strategy["signal"] = signal.reindex(strategy.index).fillna(0).astype(int)
    strategy["turnover"] = strategy["signal"].diff().abs().fillna(strategy["signal"].abs())
    strategy["strategy_return"] = (
        strategy["signal"] * strategy["simple_return"]
        - strategy["turnover"] * transaction_cost
    )
    strategy["benchmark_return"] = strategy["simple_return"]
    strategy["strategy_equity"] = (1.0 + strategy["strategy_return"]).cumprod()
    strategy["benchmark_equity"] = (1.0 + strategy["benchmark_return"]).cumprod()
    strategy["point_change"] = strategy["close"] - strategy["previous_close"]
    strategy["strategy_points"] = (
        strategy["signal"] * strategy["point_change"]
        - strategy["turnover"] * transaction_cost * strategy["previous_close"]
    )
    strategy["benchmark_points"] = strategy["point_change"]
    strategy["strategy_cumulative_points"] = strategy["strategy_points"].fillna(0.0).cumsum()
    strategy["benchmark_cumulative_points"] = strategy["benchmark_points"].fillna(0.0).cumsum()
    strategy["entry"] = (strategy["signal"].diff().fillna(strategy["signal"]) > 0).astype(int)
    strategy["exit"] = (strategy["signal"].diff().fillna(0) < 0).astype(int)
    strategy["signal_name"] = signal_name
    return strategy


def apply_strategy_rules(
    frame: pd.DataFrame,
    transaction_cost: float,
    risk_buffer: float,
) -> pd.DataFrame:
    threshold = risk_buffer * frame["forecast_volatility"]
    signal = (frame["forecast_log_return"] > threshold).astype(int)
    return finalize_long_exit_strategy(frame, signal, transaction_cost, signal_name="ito_bayes_garch")


def apply_macd_strategy(
    frame: pd.DataFrame,
    transaction_cost: float,
    fast: int = 12,
    slow: int = 26,
    signal_span: int = 9,
) -> pd.DataFrame:
    strategy = frame.copy()
    strategy["macd_fast_ema"] = strategy["close"].ewm(span=fast, adjust=False, min_periods=fast).mean()
    strategy["macd_slow_ema"] = strategy["close"].ewm(span=slow, adjust=False, min_periods=slow).mean()
    strategy["macd_line"] = strategy["macd_fast_ema"] - strategy["macd_slow_ema"]
    strategy["macd_signal_line"] = strategy["macd_line"].ewm(
        span=signal_span,
        adjust=False,
        min_periods=signal_span,
    ).mean()
    strategy["macd_histogram"] = strategy["macd_line"] - strategy["macd_signal_line"]
    raw_signal = (strategy["macd_line"] > strategy["macd_signal_line"]).astype(int)
    executable_signal = raw_signal.shift(1).fillna(0).astype(int)
    return finalize_long_exit_strategy(
        strategy,
        executable_signal,
        transaction_cost,
        signal_name=f"macd_{fast}_{slow}_{signal_span}",
    )


def max_drawdown(equity: pd.Series) -> float:
    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    return float(drawdown.min())


def drawdown_stats(equity: pd.Series) -> dict[str, float]:
    drawdown = equity / equity.cummax() - 1.0
    max_dd = float(drawdown.min())
    ulcer_index = float(np.sqrt(np.mean(np.square(np.minimum(drawdown, 0.0)))))

    durations: list[int] = []
    current = 0
    for value in drawdown:
        if value < 0:
            current += 1
        elif current:
            durations.append(current)
            current = 0
    if current:
        durations.append(current)

    negative_periods = drawdown[drawdown < 0]
    return {
        "max_drawdown": max_dd,
        "avg_drawdown": float(negative_periods.mean()) if len(negative_periods) else 0.0,
        "ulcer_index": ulcer_index,
        "max_drawdown_duration_days": float(max(durations) if durations else 0),
        "avg_drawdown_duration_days": float(np.mean(durations) if durations else 0),
    }


def annualized_metrics(returns: pd.Series, equity: pd.Series) -> dict[str, float]:
    clean = returns.dropna()
    years = len(clean) / TRADING_DAYS
    total_return = float(equity.iloc[-1] - 1.0)
    cagr = float(equity.iloc[-1] ** (1.0 / years) - 1.0) if years > 0 else np.nan
    vol = float(clean.std(ddof=1) * math.sqrt(TRADING_DAYS))
    sharpe = float(clean.mean() / clean.std(ddof=1) * math.sqrt(TRADING_DAYS)) if clean.std(ddof=1) > 0 else np.nan
    return {
        "total_return": total_return,
        "cagr": cagr,
        "annual_volatility": vol,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown(equity),
        "win_rate": float((clean > 0).mean()),
    }


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0 or pd.isna(denominator):
        return np.nan
    return float(numerator / denominator)


def advanced_return_metrics(
    frame: pd.DataFrame,
    return_col: str,
    equity_col: str,
    benchmark_col: str | None = None,
    point_col: str | None = None,
) -> dict[str, float]:
    returns = frame[return_col].dropna()
    equity = frame[equity_col].loc[returns.index]
    years = len(returns) / TRADING_DAYS
    total_return = float(equity.iloc[-1] - 1.0)
    cagr = float(equity.iloc[-1] ** (1.0 / years) - 1.0) if years > 0 and equity.iloc[-1] > 0 else np.nan
    daily_mean = float(returns.mean())
    daily_std = float(returns.std(ddof=1))
    annual_vol = daily_std * math.sqrt(TRADING_DAYS)
    annual_return_arithmetic = daily_mean * TRADING_DAYS

    downside = returns[returns < 0]
    downside_std = float(downside.std(ddof=1)) if len(downside) > 1 else 0.0
    downside_vol = downside_std * math.sqrt(TRADING_DAYS)
    gains = returns[returns > 0]
    losses = returns[returns < 0]

    dd = drawdown_stats(equity)
    sharpe = _safe_div(daily_mean, daily_std) * math.sqrt(TRADING_DAYS)
    sortino = _safe_div(daily_mean, downside_std) * math.sqrt(TRADING_DAYS)
    calmar = _safe_div(cagr, abs(dd["max_drawdown"]))
    gross_gain = float(gains.sum()) if len(gains) else 0.0
    gross_loss = abs(float(losses.sum())) if len(losses) else 0.0

    metrics = {
        "observations": float(len(returns)),
        "years": years,
        "total_return": total_return,
        "cagr": cagr,
        "annual_return_arithmetic": annual_return_arithmetic,
        "annual_volatility": annual_vol,
        "downside_volatility": downside_vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "max_drawdown": dd["max_drawdown"],
        "avg_drawdown": dd["avg_drawdown"],
        "ulcer_index": dd["ulcer_index"],
        "max_drawdown_duration_days": dd["max_drawdown_duration_days"],
        "avg_drawdown_duration_days": dd["avg_drawdown_duration_days"],
        "win_rate": float((returns > 0).mean()),
        "loss_rate": float((returns < 0).mean()),
        "avg_daily_return": daily_mean,
        "median_daily_return": float(returns.median()),
        "best_day": float(returns.max()),
        "worst_day": float(returns.min()),
        "skewness": float(returns.skew()),
        "excess_kurtosis": float(returns.kurt()),
        "var_95_daily": float(returns.quantile(0.05)),
        "cvar_95_daily": float(returns[returns <= returns.quantile(0.05)].mean()),
        "var_99_daily": float(returns.quantile(0.01)),
        "cvar_99_daily": float(returns[returns <= returns.quantile(0.01)].mean()),
        "profit_factor": _safe_div(gross_gain, gross_loss),
        "avg_win": float(gains.mean()) if len(gains) else 0.0,
        "avg_loss": float(losses.mean()) if len(losses) else 0.0,
        "payoff_ratio": _safe_div(float(gains.mean()) if len(gains) else 0.0, abs(float(losses.mean())) if len(losses) else 0.0),
        "omega_ratio_0": _safe_div(gross_gain, gross_loss),
    }

    if point_col is not None and point_col in frame.columns:
        points = frame[point_col].loc[returns.index].dropna()
        total_points = float(points.sum()) if len(points) else np.nan
        metrics.update(
            {
                "total_points": total_points,
                "annual_points": total_points / years if years > 0 else np.nan,
                "avg_daily_points": float(points.mean()) if len(points) else np.nan,
                "best_day_points": float(points.max()) if len(points) else np.nan,
                "worst_day_points": float(points.min()) if len(points) else np.nan,
            }
        )

    if benchmark_col is not None:
        benchmark = frame[benchmark_col].loc[returns.index].dropna()
        aligned = pd.concat([returns, benchmark], axis=1).dropna()
        aligned.columns = ["strategy", "benchmark"]
        active = aligned["strategy"] - aligned["benchmark"]
        beta = (
            float(np.cov(aligned["strategy"], aligned["benchmark"], ddof=1)[0, 1] / aligned["benchmark"].var(ddof=1))
            if len(aligned) > 2 and aligned["benchmark"].var(ddof=1) > 0
            else np.nan
        )
        alpha_daily = float(aligned["strategy"].mean() - beta * aligned["benchmark"].mean()) if not pd.isna(beta) else np.nan
        tracking_error = float(active.std(ddof=1) * math.sqrt(TRADING_DAYS)) if len(active) > 1 else np.nan
        up = aligned[aligned["benchmark"] > 0]
        down = aligned[aligned["benchmark"] < 0]
        metrics.update(
            {
                "beta_to_benchmark": beta,
                "alpha_annual": alpha_daily * TRADING_DAYS if not pd.isna(alpha_daily) else np.nan,
                "correlation_to_benchmark": float(aligned["strategy"].corr(aligned["benchmark"])),
                "tracking_error": tracking_error,
                "information_ratio": _safe_div(float(active.mean()) * TRADING_DAYS, tracking_error),
                "active_return_annual": float(active.mean()) * TRADING_DAYS,
                "up_capture": _safe_div(float(up["strategy"].mean()), float(up["benchmark"].mean())) if len(up) else np.nan,
                "down_capture": _safe_div(float(down["strategy"].mean()), float(down["benchmark"].mean())) if len(down) else np.nan,
            }
        )

    return metrics


def trade_metrics(frame: pd.DataFrame) -> dict[str, float]:
    trades: list[dict[str, float]] = []
    in_trade = False
    start_date = None
    trade_returns: list[float] = []
    trade_points: list[float] = []

    for _, row in frame.iterrows():
        if row["signal"] == 1 and not in_trade:
            in_trade = True
            start_date = row["date"]
            trade_returns = []
            trade_points = []
        if in_trade:
            trade_returns.append(float(row["strategy_return"]))
            trade_points.append(float(row.get("strategy_points", 0.0)))
        if in_trade and row["exit"] == 1:
            trades.append(
                {
                    "start": start_date,
                    "end": row["date"],
                    "days": len(trade_returns),
                    "return": float(np.prod(1.0 + np.asarray(trade_returns)) - 1.0),
                    "points": float(np.sum(trade_points)),
                }
            )
            in_trade = False
            start_date = None
            trade_returns = []
            trade_points = []

    if in_trade and trade_returns:
        trades.append(
            {
                "start": start_date,
                "end": frame["date"].iloc[-1],
                "days": len(trade_returns),
                "return": float(np.prod(1.0 + np.asarray(trade_returns)) - 1.0),
                "points": float(np.sum(trade_points)),
            }
        )

    if not trades:
        return {
            "trades": 0.0,
            "trade_win_rate": np.nan,
            "avg_trade_return": np.nan,
            "median_trade_return": np.nan,
            "best_trade": np.nan,
            "worst_trade": np.nan,
            "avg_holding_days": 0.0,
            "median_holding_days": 0.0,
            "expectancy_per_trade": np.nan,
            "avg_trade_points": np.nan,
            "median_trade_points": np.nan,
            "best_trade_points": np.nan,
            "worst_trade_points": np.nan,
        }

    trade_df = pd.DataFrame(trades)
    winners = trade_df[trade_df["return"] > 0]
    losers = trade_df[trade_df["return"] < 0]
    win_rate = float(len(winners) / len(trade_df))
    avg_win = float(winners["return"].mean()) if len(winners) else 0.0
    avg_loss = float(losers["return"].mean()) if len(losers) else 0.0
    return {
        "trades": float(len(trade_df)),
        "trade_win_rate": win_rate,
        "avg_trade_return": float(trade_df["return"].mean()),
        "median_trade_return": float(trade_df["return"].median()),
        "best_trade": float(trade_df["return"].max()),
        "worst_trade": float(trade_df["return"].min()),
        "avg_holding_days": float(trade_df["days"].mean()),
        "median_holding_days": float(trade_df["days"].median()),
        "expectancy_per_trade": win_rate * avg_win + (1.0 - win_rate) * avg_loss,
        "avg_trade_points": float(trade_df["points"].mean()),
        "median_trade_points": float(trade_df["points"].median()),
        "best_trade_points": float(trade_df["points"].max()),
        "worst_trade_points": float(trade_df["points"].min()),
    }


def forecast_metrics(pred: pd.DataFrame) -> dict[str, float]:
    test = pred[pred["split"] == "test"].dropna(subset=["close", "forecast_close", "log_return"])
    rmse = math.sqrt(mean_squared_error(test["close"], test["forecast_close"]))
    return {
        "rmse_close": float(rmse),
        "mae_close": float(mean_absolute_error(test["close"], test["forecast_close"])),
        "r2_close": float(r2_score(test["close"], test["forecast_close"])),
        "directional_accuracy": float((test["direction_actual"] == test["direction_forecast"]).mean()),
        "mean_forecast_daily_return": float(test["forecast_log_return"].mean()),
        "mean_actual_daily_return": float(test["log_return"].mean()),
        "mean_forecast_daily_volatility": float(test["forecast_volatility"].mean()),
    }


def save_forecast_plot(pred: pd.DataFrame, split_date: pd.Timestamp, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(pred["date"], pred["close"], label="Actual VN-Index", color="#1f2937", linewidth=1.6)
    train_mask = pred["split"] == "train"
    test_mask = pred["split"] == "test"
    ax.plot(
        pred.loc[train_mask, "date"],
        pred.loc[train_mask, "forecast_close"],
        label="Train one-step fit",
        color="#2563eb",
        alpha=0.55,
        linewidth=1.1,
    )
    ax.plot(
        pred.loc[test_mask, "date"],
        pred.loc[test_mask, "forecast_close"],
        label="Test forecast",
        color="#dc2626",
        linewidth=1.4,
    )
    ax.fill_between(
        pred.loc[test_mask, "date"],
        pred.loc[test_mask, "forecast_close_p05"],
        pred.loc[test_mask, "forecast_close_p95"],
        color="#fca5a5",
        alpha=0.28,
        label="90% Brownian predictive band",
    )
    ax.axvline(split_date, color="#111827", linestyle="--", linewidth=1.0, label="Train/Test split")
    ax.set_title("VN-Index Forecast: Ito GBM + Bayes-GARCH")
    ax.set_ylabel("VN-Index close")
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_dir / "forecast_train_test.png", dpi=180)
    plt.close(fig)


def save_backtest_plot(strategy: pd.DataFrame, output_dir: Path, macd_strategy: pd.DataFrame | None = None) -> None:
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(strategy["date"], strategy["strategy_equity"], label="Ito Bayes-GARCH strategy", color="#047857")
    if macd_strategy is not None:
        ax.plot(
            macd_strategy["date"],
            macd_strategy["strategy_equity"],
            label="MACD(6,26,12) long/exit",
            color="#ea580c",
            linewidth=1.2,
        )
    ax.plot(strategy["date"], strategy["benchmark_equity"], label="Buy & hold VN-Index", color="#334155")
    ax.set_title("Backtest Equity Curve on Test Set")
    ax.set_ylabel("Growth of 1.0 VND")
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_dir / "backtest_equity_curve.png", dpi=180)
    plt.close(fig)


def save_signal_plot(strategy: pd.DataFrame, output_dir: Path) -> None:
    entries = strategy[strategy["entry"] == 1]
    exits = strategy[strategy["exit"] == 1]
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(strategy["date"], strategy["close"], label="VN-Index", color="#1f2937", linewidth=1.4)
    ax.scatter(entries["date"], entries["close"], label="Entry", marker="^", color="#16a34a", s=42, zorder=3)
    ax.scatter(exits["date"], exits["close"], label="Exit", marker="v", color="#dc2626", s=42, zorder=3)
    ax.set_title("Long/Cash Trading Signals from Forecasted Ito Drift")
    ax.set_ylabel("VN-Index close")
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_dir / "signals_on_price.png", dpi=180)
    plt.close(fig)


def save_macd_signal_plot(macd_strategy: pd.DataFrame, output_dir: Path) -> None:
    entries = macd_strategy[macd_strategy["entry"] == 1]
    exits = macd_strategy[macd_strategy["exit"] == 1]
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(macd_strategy["date"], macd_strategy["close"], label="VN-Index", color="#1f2937", linewidth=1.4)
    ax.scatter(entries["date"], entries["close"], label="MACD long", marker="^", color="#16a34a", s=42, zorder=3)
    ax.scatter(exits["date"], exits["close"], label="MACD exit", marker="v", color="#dc2626", s=42, zorder=3)
    ax.set_title("MACD(6,26,12) Long/Exit Signals on VN-Index")
    ax.set_ylabel("VN-Index close")
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_dir / "macd_signals_on_price.png", dpi=180)
    plt.close(fig)


def save_macd_indicator_plot(macd_strategy: pd.DataFrame, output_dir: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True, gridspec_kw={"height_ratios": [2.0, 1.2]})
    axes[0].plot(macd_strategy["date"], macd_strategy["close"], color="#1f2937", linewidth=1.3, label="VN-Index")
    axes[0].set_title("VN-Index and MACD(6,26,12) Indicator")
    axes[0].set_ylabel("Close")
    axes[0].grid(alpha=0.25)
    axes[0].legend(loc="best")

    hist = macd_strategy["macd_histogram"]
    colors = np.where(hist >= 0, "#16a34a", "#dc2626")
    axes[1].bar(macd_strategy["date"], hist, color=colors, alpha=0.5, width=1.0, label="Histogram")
    axes[1].plot(macd_strategy["date"], macd_strategy["macd_line"], color="#2563eb", linewidth=1.2, label="MACD line")
    axes[1].plot(
        macd_strategy["date"],
        macd_strategy["macd_signal_line"],
        color="#ea580c",
        linewidth=1.2,
        label="Signal line",
    )
    axes[1].axhline(0, color="#111827", linewidth=0.8)
    axes[1].set_ylabel("MACD")
    axes[1].grid(alpha=0.25)
    axes[1].legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_dir / "macd_indicator_test.png", dpi=180)
    plt.close(fig)


def save_drawdown_comparison_plot(
    strategy: pd.DataFrame,
    macd_strategy: pd.DataFrame,
    output_dir: Path,
) -> None:
    def drawdown(equity: pd.Series) -> pd.Series:
        return equity / equity.cummax() - 1.0

    fig, ax = plt.subplots(figsize=(13, 5.5))
    ax.plot(strategy["date"], drawdown(strategy["strategy_equity"]), label="Ito Bayes-GARCH", color="#047857")
    ax.plot(macd_strategy["date"], drawdown(macd_strategy["strategy_equity"]), label="MACD(6,26,12)", color="#ea580c")
    ax.plot(strategy["date"], drawdown(strategy["benchmark_equity"]), label="Buy & Hold", color="#334155")
    ax.set_title("Drawdown Comparison on Test Set")
    ax.set_ylabel("Drawdown")
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_dir / "drawdown_comparison_test.png", dpi=180)
    plt.close(fig)


def save_rolling_risk_plot(
    strategy: pd.DataFrame,
    macd_strategy: pd.DataFrame,
    output_dir: Path,
    window: int = 63,
) -> None:
    fig, ax = plt.subplots(figsize=(13, 5.5))
    ito_vol = strategy["strategy_return"].rolling(window).std() * math.sqrt(TRADING_DAYS)
    macd_vol = macd_strategy["strategy_return"].rolling(window).std() * math.sqrt(TRADING_DAYS)
    bh_vol = strategy["benchmark_return"].rolling(window).std() * math.sqrt(TRADING_DAYS)
    ax.plot(strategy["date"], ito_vol, label="Ito Bayes-GARCH", color="#047857")
    ax.plot(macd_strategy["date"], macd_vol, label="MACD(6,26,12)", color="#ea580c")
    ax.plot(strategy["date"], bh_vol, label="Buy & Hold", color="#334155")
    ax.set_title(f"Rolling {window}-Session Annualized Volatility on Test Set")
    ax.set_ylabel("Annualized volatility")
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_dir / "rolling_volatility_comparison_test.png", dpi=180)
    plt.close(fig)


def save_return_distribution_plot(
    strategy: pd.DataFrame,
    macd_strategy: pd.DataFrame,
    output_dir: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.5))
    series = [
        ("Ito Bayes-GARCH", strategy["strategy_return"], "#047857"),
        ("MACD(6,26,12)", macd_strategy["strategy_return"], "#ea580c"),
        ("Buy & Hold", strategy["benchmark_return"], "#334155"),
    ]
    bins = np.linspace(-0.07, 0.07, 70)
    for label, returns, color in series:
        ax.hist(returns.dropna(), bins=bins, alpha=0.32, density=True, label=label, color=color)
    ax.axvline(0, color="#111827", linewidth=0.8)
    ax.set_title("Daily Return Distribution on Test Set")
    ax.set_xlabel("Daily return")
    ax.set_ylabel("Density")
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.grid(alpha=0.2)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_dir / "return_distribution_test.png", dpi=180)
    plt.close(fig)


def save_volatility_plot(pred: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(13, 5))
    annual_vol = pred["forecast_volatility"] * math.sqrt(TRADING_DAYS)
    ax.plot(pred["date"], annual_vol, color="#7c3aed", linewidth=1.2)
    ax.set_title("Forecast Annualized Volatility from Bayes-GARCH")
    ax.set_ylabel("Annualized volatility")
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "forecast_volatility.png", dpi=180)
    plt.close(fig)


def format_pct(value: float) -> str:
    if pd.isna(value):
        return "nan"
    return f"{value:.2%}"


def save_report(
    cfg: StrategyConfig,
    df: pd.DataFrame,
    train: pd.DataFrame,
    test: pd.DataFrame,
    result,
    pred: pd.DataFrame,
    strategy: pd.DataFrame,
    f_metrics: dict[str, float],
    s_metrics: dict[str, float],
    m_metrics: dict[str, float],
    b_metrics: dict[str, float],
) -> None:
    output_dir = cfg.output_dir
    params = result.params.to_dict()
    report = f"""# VN-Index Stochastic Calculus Strategy Report

## Model

- Price process: `dS/S = mu dt + sigma dW`, with Brownian motion `W_t`.
- Ito lemma: `d log(S) = (mu - 0.5 sigma^2)dt + sigma dW`.
- Return engine: Student-t GARCH(1,1), then an approximate Bayesian posterior around the fitted parameters.
- Drift forecast: Bayesian rolling mean over `{cfg.drift_window}` sessions, shrunk toward the train-set prior with strength `{cfg.drift_prior_strength}`.
- Signal: long VN-Index when forecast log-return is greater than `{cfg.risk_buffer:.2f}` times forecast daily volatility; otherwise cash.
- Transaction cost assumption: `{cfg.transaction_cost:.2%}` per position change.

## Data Split

- Data file: `{cfg.data_path}`
- Clean sample: `{len(df):,}` daily returns from `{df['date'].min().date()}` to `{df['date'].max().date()}`
- Modeling start date: `{cfg.start_date}`
- Train: `{len(train):,}` rows from `{train['date'].min().date()}` to `{train['date'].max().date()}`
- Test: `{len(test):,}` rows from `{test['date'].min().date()}` to `{test['date'].max().date()}`

## Fitted Bayes-GARCH Center

- mu: `{params.get('mu', np.nan):.6f}` percent daily
- omega: `{params.get('omega', np.nan):.6f}`
- alpha[1]: `{params.get('alpha[1]', np.nan):.6f}`
- beta[1]: `{params.get('beta[1]', np.nan):.6f}`
- nu: `{params.get('nu', np.nan):.3f}`

## Forecast Quality on Test

- RMSE close: `{f_metrics['rmse_close']:.3f}`
- MAE close: `{f_metrics['mae_close']:.3f}`
- R2 close: `{f_metrics['r2_close']:.4f}`
- Directional accuracy: `{format_pct(f_metrics['directional_accuracy'])}`
- Mean forecast daily log-return: `{format_pct(f_metrics['mean_forecast_daily_return'])}`
- Mean actual daily log-return: `{format_pct(f_metrics['mean_actual_daily_return'])}`
- Mean forecast daily volatility: `{format_pct(f_metrics['mean_forecast_daily_volatility'])}`

## Backtest on Test

| Metric | Ito Bayes-GARCH Strategy | MACD(6,26,12) Long/Exit | Buy & Hold |
|---|---:|---:|---:|
| Total return | {format_pct(s_metrics['total_return'])} | {format_pct(m_metrics['total_return'])} | {format_pct(b_metrics['total_return'])} |
| CAGR | {format_pct(s_metrics['cagr'])} | {format_pct(m_metrics['cagr'])} | {format_pct(b_metrics['cagr'])} |
| Annual volatility | {format_pct(s_metrics['annual_volatility'])} | {format_pct(m_metrics['annual_volatility'])} | {format_pct(b_metrics['annual_volatility'])} |
| Sharpe | {s_metrics['sharpe']:.3f} | {m_metrics['sharpe']:.3f} | {b_metrics['sharpe']:.3f} |
| Max drawdown | {format_pct(s_metrics['max_drawdown'])} | {format_pct(m_metrics['max_drawdown'])} | {format_pct(b_metrics['max_drawdown'])} |
| Win rate | {format_pct(s_metrics['win_rate'])} | {format_pct(m_metrics['win_rate'])} | {format_pct(b_metrics['win_rate'])} |

## Files

- `predictions.csv`: train/test forecasts and predictive bands.
- `strategy_backtest.csv`: test-set signals, returns, and equity curves.
- `full_data_backtest.csv`: full-sample signals, returns, and equity curves.
- `macd_strategy_backtest.csv`: test-set MACD(6,26,12) long/exit signals and equity curve.
- `macd_full_data_backtest.csv`: full-sample MACD(6,26,12) long/exit backtest.
- `advanced_backtest_metrics.csv`: raw numeric full/test advanced metrics.
- `advanced_backtest_metrics_formatted.csv`: presentation-ready full/test metrics.
- `advanced_backtest_metrics.md`: Markdown table for review.
- `forecast_train_test.png`: actual close, train fit, test forecast, and 90% Brownian band.
- `backtest_equity_curve.png`: strategy versus buy-and-hold.
- `signals_on_price.png`: entry and exit points.
- `macd_indicator_test.png`: MACD line, signal line, histogram, and VN-Index price.
- `macd_signals_on_price.png`: MACD long/exit points on VN-Index price.
- `drawdown_comparison_test.png`: drawdown comparison across Ito, MACD, and buy-and-hold.
- `rolling_volatility_comparison_test.png`: 63-session rolling annualized volatility.
- `return_distribution_test.png`: daily return distribution comparison.
- `forecast_volatility.png`: annualized Bayes-GARCH volatility estimate.

## Reading the Result

This is a research backtest, not an execution-ready trading system. The Bayesian
part is an asymptotic posterior approximation around GARCH maximum likelihood,
chosen because it is light enough for a laptop environment and does not require
PyMC/MCMC. A stronger next step would be walk-forward refitting, regime filters,
and stress tests around transaction cost and signal thresholds.
"""
    (output_dir / "report.md").write_text(report, encoding="utf-8")


METRIC_LABELS = {
    "observations": "Observations",
    "years": "Years",
    "exposure": "Market exposure",
    "entries": "Entries",
    "exits": "Exits",
    "avg_daily_turnover": "Average daily turnover",
    "annual_turnover": "Annual turnover",
    "total_points": "Total VN-Index points",
    "annual_points": "Annual VN-Index points",
    "avg_daily_points": "Average daily points",
    "best_day_points": "Best day points",
    "worst_day_points": "Worst day points",
    "total_return": "Total return",
    "cagr": "CAGR",
    "annual_return_arithmetic": "Annualized mean return",
    "annual_volatility": "Annual volatility",
    "downside_volatility": "Downside volatility",
    "sharpe": "Sharpe ratio",
    "sortino": "Sortino ratio",
    "calmar": "Calmar ratio",
    "max_drawdown": "Max drawdown",
    "avg_drawdown": "Average drawdown",
    "ulcer_index": "Ulcer index",
    "max_drawdown_duration_days": "Max drawdown duration days",
    "avg_drawdown_duration_days": "Average drawdown duration days",
    "win_rate": "Daily win rate",
    "loss_rate": "Daily loss rate",
    "avg_daily_return": "Average daily return",
    "median_daily_return": "Median daily return",
    "best_day": "Best day",
    "worst_day": "Worst day",
    "skewness": "Skewness",
    "excess_kurtosis": "Excess kurtosis",
    "var_95_daily": "Daily VaR 95%",
    "cvar_95_daily": "Daily CVaR 95%",
    "var_99_daily": "Daily VaR 99%",
    "cvar_99_daily": "Daily CVaR 99%",
    "profit_factor": "Profit factor",
    "avg_win": "Average winning day",
    "avg_loss": "Average losing day",
    "payoff_ratio": "Payoff ratio",
    "omega_ratio_0": "Omega ratio, threshold 0",
    "beta_to_benchmark": "Beta to buy-and-hold",
    "alpha_annual": "Annual alpha",
    "correlation_to_benchmark": "Correlation to benchmark",
    "tracking_error": "Tracking error",
    "information_ratio": "Information ratio",
    "active_return_annual": "Annual active return",
    "up_capture": "Up capture",
    "down_capture": "Down capture",
    "trades": "Trades",
    "trade_win_rate": "Trade win rate",
    "avg_trade_return": "Average trade return",
    "median_trade_return": "Median trade return",
    "best_trade": "Best trade",
    "worst_trade": "Worst trade",
    "avg_holding_days": "Average holding days",
    "median_holding_days": "Median holding days",
    "expectancy_per_trade": "Expectancy per trade",
    "avg_trade_points": "Average trade points",
    "median_trade_points": "Median trade points",
    "best_trade_points": "Best trade points",
    "worst_trade_points": "Worst trade points",
}


PERCENT_METRICS = {
    "exposure",
    "avg_daily_turnover",
    "annual_turnover",
    "total_return",
    "cagr",
    "annual_return_arithmetic",
    "annual_volatility",
    "downside_volatility",
    "max_drawdown",
    "avg_drawdown",
    "ulcer_index",
    "win_rate",
    "loss_rate",
    "avg_daily_return",
    "median_daily_return",
    "best_day",
    "worst_day",
    "var_95_daily",
    "cvar_95_daily",
    "var_99_daily",
    "cvar_99_daily",
    "avg_win",
    "avg_loss",
    "alpha_annual",
    "tracking_error",
    "active_return_annual",
    "up_capture",
    "down_capture",
    "trade_win_rate",
    "avg_trade_return",
    "median_trade_return",
    "best_trade",
    "worst_trade",
    "expectancy_per_trade",
}


POINT_METRICS = {
    "total_points",
    "annual_points",
    "avg_daily_points",
    "best_day_points",
    "worst_day_points",
    "avg_trade_points",
    "median_trade_points",
    "best_trade_points",
    "worst_trade_points",
}


def _fmt_metric(metric: str, value: float) -> str:
    if pd.isna(value):
        return ""
    if metric in PERCENT_METRICS:
        return f"{value:.2%}"
    if metric in POINT_METRICS:
        return f"{value:,.2f}"
    if metric in {
        "observations",
        "entries",
        "exits",
        "trades",
        "max_drawdown_duration_days",
        "avg_drawdown_duration_days",
        "avg_holding_days",
        "median_holding_days",
    }:
        return f"{value:,.1f}"
    return f"{value:.3f}"


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    headers = list(df.columns)
    rows = [[str(value) for value in row] for row in df.to_numpy()]
    widths = [
        max(len(str(header)), *(len(row[col_idx]) for row in rows))
        for col_idx, header in enumerate(headers)
    ]
    header_line = "| " + " | ".join(str(header).ljust(widths[idx]) for idx, header in enumerate(headers)) + " |"
    separator = "| " + " | ".join("-" * widths[idx] for idx in range(len(headers))) + " |"
    body = [
        "| " + " | ".join(row[idx].ljust(widths[idx]) for idx in range(len(headers))) + " |"
        for row in rows
    ]
    return "\n".join([header_line, separator, *body])


def _add_operational_metrics(metrics: dict[str, float], frame: pd.DataFrame, is_strategy: bool) -> dict[str, float]:
    out = dict(metrics)
    years = max(len(frame) / TRADING_DAYS, 1e-9)
    if is_strategy:
        out.update(
            {
                "exposure": float(frame["signal"].mean()),
                "entries": float(frame["entry"].sum()),
                "exits": float(frame["exit"].sum()),
                "avg_daily_turnover": float(frame["turnover"].mean()),
                "annual_turnover": float(frame["turnover"].sum() / years),
            }
        )
        out.update(trade_metrics(frame))
    else:
        out.update(
            {
                "exposure": 1.0,
                "entries": np.nan,
                "exits": np.nan,
                "avg_daily_turnover": 0.0,
                "annual_turnover": 0.0,
                "trades": np.nan,
                "trade_win_rate": np.nan,
                "avg_trade_return": np.nan,
                "median_trade_return": np.nan,
                "best_trade": np.nan,
                "worst_trade": np.nan,
                "avg_holding_days": np.nan,
                "median_holding_days": np.nan,
                "expectancy_per_trade": np.nan,
                "avg_trade_points": np.nan,
                "median_trade_points": np.nan,
                "best_trade_points": np.nan,
                "worst_trade_points": np.nan,
            }
        )
    return out


def save_advanced_backtest_tables(
    full_ito: pd.DataFrame,
    test_ito: pd.DataFrame,
    full_macd: pd.DataFrame,
    test_macd: pd.DataFrame,
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_order = list(METRIC_LABELS.keys())
    portfolios = {
        "Full Data - Ito": _add_operational_metrics(
            advanced_return_metrics(
                full_ito,
                return_col="strategy_return",
                equity_col="strategy_equity",
                benchmark_col="benchmark_return",
                point_col="strategy_points",
            ),
            full_ito,
            is_strategy=True,
        ),
        "Full Data - MACD(6,26,12)": _add_operational_metrics(
            advanced_return_metrics(
                full_macd,
                return_col="strategy_return",
                equity_col="strategy_equity",
                benchmark_col="benchmark_return",
                point_col="strategy_points",
            ),
            full_macd,
            is_strategy=True,
        ),
        "Full Data - Buy & Hold": _add_operational_metrics(
            advanced_return_metrics(
                full_ito,
                return_col="benchmark_return",
                equity_col="benchmark_equity",
                point_col="benchmark_points",
            ),
            full_ito,
            is_strategy=False,
        ),
        "Test - Ito": _add_operational_metrics(
            advanced_return_metrics(
                test_ito,
                return_col="strategy_return",
                equity_col="strategy_equity",
                benchmark_col="benchmark_return",
                point_col="strategy_points",
            ),
            test_ito,
            is_strategy=True,
        ),
        "Test - MACD(6,26,12)": _add_operational_metrics(
            advanced_return_metrics(
                test_macd,
                return_col="strategy_return",
                equity_col="strategy_equity",
                benchmark_col="benchmark_return",
                point_col="strategy_points",
            ),
            test_macd,
            is_strategy=True,
        ),
        "Test - Buy & Hold": _add_operational_metrics(
            advanced_return_metrics(
                test_ito,
                return_col="benchmark_return",
                equity_col="benchmark_equity",
                point_col="benchmark_points",
            ),
            test_ito,
            is_strategy=False,
        ),
    }

    raw_rows: list[dict[str, object]] = []
    formatted_rows: list[dict[str, object]] = []
    for metric in metric_order:
        label = METRIC_LABELS[metric]
        formatted_row = {"Metric": label}
        for scope, metrics in portfolios.items():
            value = metrics.get(metric, np.nan)
            raw_rows.append({"portfolio": scope, "metric": metric, "metric_label": label, "value": value})
            formatted_row[scope] = _fmt_metric(metric, value)
        formatted_rows.append(formatted_row)

    raw = pd.DataFrame(raw_rows)
    formatted = pd.DataFrame(formatted_rows)
    raw.to_csv(output_dir / "advanced_backtest_metrics.csv", index=False)
    formatted.to_csv(output_dir / "advanced_backtest_metrics_formatted.csv", index=False)

    markdown = "# Advanced Backtest Metrics\n\n"
    markdown += "So sanh Ito Bayes-GARCH, MACD(6,26,12) long/exit va buy-and-hold tren Full Data va rieng Test.\n\n"
    markdown += dataframe_to_markdown(formatted)
    markdown += "\n"
    (output_dir / "advanced_backtest_metrics.md").write_text(markdown, encoding="utf-8")
    return raw, formatted


def run(cfg: StrategyConfig) -> dict[str, object]:
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    df = load_vnindex_csv(cfg.data_path)
    df = df[df["date"] >= pd.Timestamp(cfg.start_date)].reset_index(drop=True)
    train, test = chronological_split(df, cfg.train_ratio)

    result = fit_garch(train["log_return"])
    posterior = sample_garch_posterior(result, cfg.posterior_samples, cfg.random_state)
    drift_prior_mean = float(train["log_return"].mean())
    train_forecast = in_sample_garch_forecast(
        result=result,
        full_returns=df["log_return"],
        train=train,
        drift_prior_mean=drift_prior_mean,
        drift_prior_strength=cfg.drift_prior_strength,
        drift_window=cfg.drift_window,
    )
    test_forecast = recursive_bayes_garch_forecast(
        result=result,
        posterior=posterior,
        full_returns=df["log_return"],
        test_index=test.index,
        drift_prior_mean=drift_prior_mean,
        drift_prior_strength=cfg.drift_prior_strength,
        drift_window=cfg.drift_window,
        random_state=cfg.random_state + 1,
    )

    pred, full_strategy, strategy, full_macd, macd_strategy = build_prediction_table(
        df=df,
        train=train,
        test=test,
        train_forecast=train_forecast,
        test_forecast=test_forecast,
        transaction_cost=cfg.transaction_cost,
        risk_buffer=cfg.risk_buffer,
        macd_fast=cfg.macd_fast,
        macd_slow=cfg.macd_slow,
        macd_signal=cfg.macd_signal,
    )

    f_metrics = forecast_metrics(pred)
    s_metrics = annualized_metrics(strategy["strategy_return"], strategy["strategy_equity"])
    b_metrics = annualized_metrics(strategy["benchmark_return"], strategy["benchmark_equity"])
    m_metrics = annualized_metrics(macd_strategy["strategy_return"], macd_strategy["strategy_equity"])
    advanced_raw, _ = save_advanced_backtest_tables(full_strategy, strategy, full_macd, macd_strategy, cfg.output_dir)

    pred.to_csv(cfg.output_dir / "predictions.csv", index=False)
    full_strategy.to_csv(cfg.output_dir / "full_data_backtest.csv", index=False)
    strategy.to_csv(cfg.output_dir / "strategy_backtest.csv", index=False)
    full_macd.to_csv(cfg.output_dir / "macd_full_data_backtest.csv", index=False)
    macd_strategy.to_csv(cfg.output_dir / "macd_strategy_backtest.csv", index=False)
    posterior.to_csv(cfg.output_dir / "bayes_garch_posterior_draws.csv", index=False)
    save_forecast_plot(pred, split_date=test["date"].iloc[0], output_dir=cfg.output_dir)
    save_backtest_plot(strategy, output_dir=cfg.output_dir, macd_strategy=macd_strategy)
    save_signal_plot(strategy, output_dir=cfg.output_dir)
    save_macd_signal_plot(macd_strategy, output_dir=cfg.output_dir)
    save_macd_indicator_plot(macd_strategy, output_dir=cfg.output_dir)
    save_drawdown_comparison_plot(strategy, macd_strategy, output_dir=cfg.output_dir)
    save_rolling_risk_plot(strategy, macd_strategy, output_dir=cfg.output_dir)
    save_return_distribution_plot(strategy, macd_strategy, output_dir=cfg.output_dir)
    save_volatility_plot(pred, output_dir=cfg.output_dir)
    save_report(cfg, df, train, test, result, pred, strategy, f_metrics, s_metrics, m_metrics, b_metrics)

    summary = {
        "rows": int(len(df)),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "train_start": str(train["date"].min().date()),
        "train_end": str(train["date"].max().date()),
        "test_start": str(test["date"].min().date()),
        "test_end": str(test["date"].max().date()),
        "forecast_metrics": f_metrics,
        "strategy_metrics": s_metrics,
        "macd_metrics": m_metrics,
        "benchmark_metrics": b_metrics,
        "advanced_metric_rows": int(len(advanced_raw)),
        "output_dir": str(cfg.output_dir),
    }
    (cfg.output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def parse_args() -> StrategyConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data.csv"), help="VN-Index CSV path")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs_stochastic_calculus"))
    parser.add_argument("--start-date", default="2006-01-01")
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--transaction-cost", type=float, default=0.0005)
    parser.add_argument("--risk-buffer", type=float, default=0.08)
    parser.add_argument("--drift-window", type=int, default=126)
    parser.add_argument("--drift-prior-strength", type=int, default=63)
    parser.add_argument("--macd-fast", type=int, default=6)
    parser.add_argument("--macd-slow", type=int, default=26)
    parser.add_argument("--macd-signal", type=int, default=12)
    parser.add_argument("--posterior-samples", type=int, default=2000)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()
    return StrategyConfig(
        data_path=args.data,
        output_dir=args.output_dir,
        start_date=args.start_date,
        train_ratio=args.train_ratio,
        transaction_cost=args.transaction_cost,
        risk_buffer=args.risk_buffer,
        drift_window=args.drift_window,
        drift_prior_strength=args.drift_prior_strength,
        macd_fast=args.macd_fast,
        macd_slow=args.macd_slow,
        macd_signal=args.macd_signal,
        posterior_samples=args.posterior_samples,
        random_state=args.random_state,
    )


def main() -> None:
    cfg = parse_args()
    summary = run(cfg)
    print("VN-Index stochastic calculus strategy completed.")
    print(f"Output directory: {summary['output_dir']}")
    print(
        f"Train: {summary['train_rows']:,} rows ({summary['train_start']} -> {summary['train_end']})"
    )
    print(f"Test : {summary['test_rows']:,} rows ({summary['test_start']} -> {summary['test_end']})")
    fm = summary["forecast_metrics"]
    sm = summary["strategy_metrics"]
    mm = summary["macd_metrics"]
    bm = summary["benchmark_metrics"]
    print(f"Forecast RMSE close: {fm['rmse_close']:.3f}")
    print(f"Directional accuracy: {fm['directional_accuracy']:.2%}")
    print(f"Ito strategy total return: {sm['total_return']:.2%}, Sharpe: {sm['sharpe']:.3f}")
    print(f"MACD(6,26,12) total return: {mm['total_return']:.2%}, Sharpe: {mm['sharpe']:.3f}")
    print(f"Buy & hold total return: {bm['total_return']:.2%}, Sharpe: {bm['sharpe']:.3f}")


if __name__ == "__main__":
    main()
