from __future__ import annotations

import math

import numpy as np
import pandas as pd

from stochastic_ito_bayes_garch_strategy import TRADING_DAYS
from .backtester import drawdown


def _safe_div(a: float, b: float) -> float:
    if b == 0 or pd.isna(b):
        return np.nan
    return float(a / b)


def _drawdown_duration(dd: pd.Series) -> tuple[float, float]:
    durations = []
    current = 0
    for value in dd:
        if value < 0:
            current += 1
        elif current:
            durations.append(current)
            current = 0
    if current:
        durations.append(current)
    return float(max(durations) if durations else 0), float(np.mean(durations) if durations else 0)


def trade_statistics(frame: pd.DataFrame) -> dict[str, float]:
    active = frame["position"] > 1e-6
    trades = []
    in_trade = False
    trade_returns: list[float] = []
    trade_points: list[float] = []
    start = None
    for _, row in frame.iterrows():
        if row["position"] > 1e-6 and not in_trade:
            in_trade = True
            start = row["date"]
            trade_returns = []
            trade_points = []
        if in_trade:
            trade_returns.append(float(row["strategy_return"]))
            trade_points.append(float(row["strategy_points"]))
        if in_trade and row["position"] <= 1e-6:
            trades.append({"start": start, "end": row["date"], "days": len(trade_returns), "return": np.prod(1.0 + np.asarray(trade_returns)) - 1.0, "points": np.sum(trade_points)})
            in_trade = False
    if in_trade and trade_returns:
        trades.append({"start": start, "end": frame["date"].iloc[-1], "days": len(trade_returns), "return": np.prod(1.0 + np.asarray(trade_returns)) - 1.0, "points": np.sum(trade_points)})
    if not trades:
        return {"number_of_trades": 0.0, "trade_hit_rate": np.nan, "avg_trade_return": np.nan, "avg_trade_points": np.nan, "avg_holding_days": np.nan}
    tdf = pd.DataFrame(trades)
    return {
        "number_of_trades": float(len(tdf)),
        "trade_hit_rate": float((tdf["return"] > 0).mean()),
        "avg_trade_return": float(tdf["return"].mean()),
        "avg_trade_points": float(tdf["points"].mean()),
        "avg_holding_days": float(tdf["days"].mean()),
    }


def performance_metrics(frame: pd.DataFrame) -> dict[str, float]:
    returns = frame["strategy_return"].fillna(0.0)
    equity = frame["strategy_equity"]
    years = len(returns) / TRADING_DAYS
    total_return = float(equity.iloc[-1] - 1.0)
    cagr = float(equity.iloc[-1] ** (1.0 / years) - 1.0) if years > 0 and equity.iloc[-1] > 0 else np.nan
    daily_mean = float(returns.mean())
    daily_std = float(returns.std(ddof=1))
    annual_vol = daily_std * math.sqrt(TRADING_DAYS)
    downside = returns[returns < 0]
    downside_std = float(downside.std(ddof=1)) if len(downside) > 1 else np.nan
    dd = drawdown(equity)
    max_dd = float(dd.min())
    max_tuw, avg_tuw = _drawdown_duration(dd)
    gains = returns[returns > 0]
    losses = returns[returns < 0]
    gross_gain = float(gains.sum()) if len(gains) else 0.0
    gross_loss = abs(float(losses.sum())) if len(losses) else 0.0
    monthly = frame.assign(month=frame["date"].dt.to_period("M")).groupby("month")["strategy_return"].apply(lambda x: (1 + x).prod() - 1)
    yearly = frame.assign(year=frame["date"].dt.year).groupby("year")["strategy_return"].apply(lambda x: (1 + x).prod() - 1)
    exposure = float(frame["position"].mean())
    out = {
        "total_return": total_return,
        "cagr": cagr,
        "annualized_volatility": annual_vol,
        "sharpe_ratio": _safe_div(daily_mean, daily_std) * math.sqrt(TRADING_DAYS),
        "sortino_ratio": _safe_div(daily_mean, downside_std) * math.sqrt(TRADING_DAYS),
        "calmar_ratio": _safe_div(cagr, abs(max_dd)),
        "max_drawdown": max_dd,
        "time_under_water_days": max_tuw,
        "avg_time_under_water_days": avg_tuw,
        "var_95_daily": float(returns.quantile(0.05)),
        "cvar_95_daily": float(returns[returns <= returns.quantile(0.05)].mean()),
        "worst_month": float(monthly.min()) if len(monthly) else np.nan,
        "worst_year": float(yearly.min()) if len(yearly) else np.nan,
        "hit_rate": float((returns > 0).mean()),
        "average_win": float(gains.mean()) if len(gains) else 0.0,
        "average_loss": float(losses.mean()) if len(losses) else 0.0,
        "profit_factor": _safe_div(gross_gain, gross_loss),
        "turnover": float(frame["turnover"].sum()),
        "annual_turnover": float(frame["turnover"].sum() / years) if years > 0 else np.nan,
        "exposure_ratio": exposure,
        "active_day_ratio": float((frame["position"] > 1e-6).mean()),
        "return_per_unit_drawdown": _safe_div(total_return, abs(max_dd)),
        "return_per_unit_exposure": _safe_div(total_return, exposure),
        "total_points": float(frame["strategy_points"].sum()),
    }
    out.update(trade_statistics(frame))
    return out


def strategy_comparison(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, frame in frames.items():
        rows.append({"strategy": name, **performance_metrics(frame)})
    return pd.DataFrame(rows)


def year_by_year_performance(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, frame in frames.items():
        for year, group in frame.groupby(frame["date"].dt.year):
            if len(group) < 20:
                continue
            temp = group.copy()
            temp["strategy_equity"] = (1.0 + temp["strategy_return"]).cumprod()
            rows.append({"year": int(year), "strategy": name, **performance_metrics(temp)})
    return pd.DataFrame(rows)


def regime_performance(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if "regime" not in frame.columns:
        return pd.DataFrame()
    for regime, group in frame.groupby("regime"):
        if len(group) < 10:
            continue
        temp = group.copy()
        temp["strategy_equity"] = (1.0 + temp["strategy_return"]).cumprod()
        rows.append({"regime": regime, "observations": len(group), **performance_metrics(temp)})
    return pd.DataFrame(rows)


def stress_period_performance(yearly: pd.DataFrame, stress_years: list[int]) -> pd.DataFrame:
    return yearly[yearly["year"].isin(stress_years)].copy()


def format_table(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    pct_cols = {
        "total_return",
        "cagr",
        "annualized_volatility",
        "downside_volatility",
        "max_drawdown",
        "var_95_daily",
        "cvar_95_daily",
        "worst_month",
        "worst_year",
        "hit_rate",
        "average_win",
        "average_loss",
        "exposure_ratio",
        "active_day_ratio",
        "trade_hit_rate",
        "avg_trade_return",
    }
    ratio_cols = {
        "sharpe_ratio",
        "sortino_ratio",
        "calmar_ratio",
        "profit_factor",
        "return_per_unit_drawdown",
        "return_per_unit_exposure",
    }
    number_cols = {
        "total_points",
        "turnover",
        "annual_turnover",
        "number_of_trades",
        "time_under_water_days",
        "avg_time_under_water_days",
        "avg_trade_points",
        "avg_holding_days",
        "observations",
    }
    for col in out.columns:
        if col == "year" or not pd.api.types.is_numeric_dtype(out[col]):
            continue
        if col in pct_cols:
            out[col] = out[col].map(lambda x: "" if pd.isna(x) else f"{x:.2%}")
        elif col in ratio_cols:
            out[col] = out[col].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
        elif col in number_cols:
            out[col] = out[col].map(lambda x: "" if pd.isna(x) else f"{x:,.2f}")
    return out
