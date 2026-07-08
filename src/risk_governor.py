from __future__ import annotations

import numpy as np
import pandas as pd

from stochastic_ito_bayes_garch_strategy import TRADING_DAYS


def compute_risk_components(frame: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    out = pd.DataFrame(index=frame.index)
    target_daily_vol = float(cfg["target_volatility"]) / np.sqrt(TRADING_DAYS)
    forecast_vol = frame["forecast_volatility"].replace(0, np.nan)
    out["volatility_scale"] = (target_daily_vol / forecast_vol).clip(upper=1.0).fillna(0.0)
    out["tail_risk_gate"] = (frame["forecast_return_p05"] >= float(cfg["loss_floor"])).astype(float)

    interval_width = (frame["forecast_return_p95"] - frame["forecast_return_p05"]).abs()
    normal_width = 3.29 * forecast_vol
    uncertainty_proxy = (interval_width / normal_width - 1.0).clip(lower=0.0).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    out["posterior_uncertainty_proxy"] = uncertainty_proxy
    penalty = 1.0 / (1.0 + float(cfg["uncertainty_penalty_k"]) * uncertainty_proxy)
    out["uncertainty_penalty"] = penalty.clip(float(cfg["uncertainty_penalty_min"]), float(cfg["uncertainty_penalty_max"]))

    window = int(cfg["volatility_percentile_window"])
    vol_threshold = frame["forecast_volatility"].rolling(window, min_periods=20).quantile(0.75).shift(1)
    out["forecast_volatility_p75"] = vol_threshold.fillna(frame["forecast_volatility"].expanding(min_periods=5).quantile(0.75))
    out["high_forecast_volatility"] = (frame["forecast_volatility"] > out["forecast_volatility_p75"]).astype(float)
    return out


def classify_regime(frame: pd.DataFrame, components: pd.DataFrame) -> pd.Series:
    regime = pd.Series("sideways", index=frame.index, dtype="object")
    trend_up = (frame["trend_strength"].fillna(0.0) > 0.05) & (frame["macd_slope_executable"].fillna(0.0) > 0)
    recovery = (frame["trend_strength"].fillna(0.0) > 0.0) & (frame["price_drawdown_recent_high"].fillna(0.0) < -0.08)
    high_vol_chop = (components["high_forecast_volatility"] > 0) & (frame["macd_slope_executable"].fillna(0.0).abs() < frame["macd_line"].diff().abs().rolling(63, min_periods=10).median().fillna(0.0))
    panic = (frame["forecast_return_p05"] < -0.02) | (frame["price_drawdown_recent_high"].fillna(0.0) < -0.20)
    regime.loc[trend_up] = "trend_up"
    regime.loc[recovery] = "recovery"
    regime.loc[high_vol_chop] = "high_vol_chop"
    regime.loc[panic] = "panic"
    return regime


def build_full_defensive_position(
    frame: pd.DataFrame,
    macd_signal: pd.Series,
    components: pd.DataFrame,
    cfg: dict,
    transaction_cost: float,
) -> tuple[pd.Series, pd.DataFrame]:
    position = pd.Series(0.0, index=frame.index)
    diagnostics = pd.DataFrame(index=frame.index)
    equity = 1.0
    peak = 1.0
    previous_position = 0.0
    entry_price: float | None = None

    for idx, row in frame.iterrows():
        base_position = float(macd_signal.loc[idx])
        base_position *= float(components.loc[idx, "volatility_scale"])
        base_position *= float(components.loc[idx, "uncertainty_penalty"])
        base_position *= float(components.loc[idx, "tail_risk_gate"])
        desired = float(np.clip(base_position, 0.0, 1.0))

        previous_close = float(row.get("previous_close", row["close"]))
        open_trade_return = 0.0
        profit_cap = 1.0
        if previous_position > 1e-6 and entry_price is not None and entry_price > 0:
            open_trade_return = previous_close / entry_price - 1.0
            if (
                open_trade_return > float(cfg["profit_lock_threshold"])
                and row["forecast_volatility"] > components.loc[idx, "forecast_volatility_p75"]
            ):
                profit_cap = 0.5
                desired = min(desired, profit_cap)

        equity_dd_before = equity / peak - 1.0
        equity_cap = 1.0
        if equity_dd_before < -float(cfg["danger_drawdown"]):
            equity_cap = 0.0
            desired = 0.0
        elif equity_dd_before < -float(cfg["warning_drawdown"]):
            equity_cap = 0.5
            desired = min(desired, equity_cap)

        if previous_position <= 1e-6 and desired > 1e-6:
            entry_price = previous_close
        elif desired <= 1e-6:
            entry_price = None

        turnover = abs(desired - previous_position)
        day_return = desired * float(row["simple_return"]) - turnover * transaction_cost
        equity *= 1.0 + day_return
        peak = max(peak, equity)

        position.loc[idx] = desired
        diagnostics.loc[idx, "base_defensive_position"] = base_position
        diagnostics.loc[idx, "profit_protection_cap"] = profit_cap
        diagnostics.loc[idx, "equity_protection_cap"] = equity_cap
        diagnostics.loc[idx, "open_trade_return_before"] = open_trade_return
        diagnostics.loc[idx, "equity_drawdown_before"] = equity_dd_before
        previous_position = desired

    return position, diagnostics
