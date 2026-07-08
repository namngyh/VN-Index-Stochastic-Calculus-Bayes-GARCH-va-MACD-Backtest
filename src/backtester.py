from __future__ import annotations

import numpy as np
import pandas as pd


def backtest_position(
    frame: pd.DataFrame,
    position: pd.Series,
    transaction_cost: float,
    strategy_name: str,
) -> pd.DataFrame:
    out = frame.copy()
    pos = position.reindex(out.index).fillna(0.0).astype(float).clip(0.0, 1.0)
    out["strategy"] = strategy_name
    out["position"] = pos
    out["signal"] = pos
    out["turnover"] = pos.diff().abs().fillna(pos.abs())
    out["strategy_return"] = pos * out["simple_return"].fillna(0.0) - out["turnover"] * transaction_cost
    out["benchmark_return"] = out["simple_return"].fillna(0.0)
    out["strategy_equity"] = (1.0 + out["strategy_return"]).cumprod()
    out["benchmark_equity"] = (1.0 + out["benchmark_return"]).cumprod()
    previous_close = out["previous_close"].fillna(out["close"] / (1.0 + out["simple_return"]))
    out["point_change"] = out["close"] - previous_close
    out["strategy_points"] = pos * out["point_change"] - out["turnover"] * transaction_cost * previous_close
    out["benchmark_points"] = out["point_change"]
    out["strategy_cumulative_points"] = out["strategy_points"].fillna(0.0).cumsum()
    out["benchmark_cumulative_points"] = out["benchmark_points"].fillna(0.0).cumsum()
    active = pos > 1e-6
    prev_active = active.shift(1, fill_value=False)
    out["entry"] = (active & ~prev_active).astype(int)
    out["exit"] = (~active & prev_active).astype(int)
    return out


def drawdown(equity: pd.Series) -> pd.Series:
    return equity / equity.cummax() - 1.0
