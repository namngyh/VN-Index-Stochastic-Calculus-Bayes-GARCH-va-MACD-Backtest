from __future__ import annotations

import numpy as np
import pandas as pd

from stochastic_ito_bayes_garch_strategy import TRADING_DAYS


def add_macd_features(df: pd.DataFrame, fast: int, slow: int, signal_span: int) -> pd.DataFrame:
    out = df.copy()
    out["macd_fast_ema"] = out["close"].ewm(span=fast, adjust=False, min_periods=fast).mean()
    out["macd_slow_ema"] = out["close"].ewm(span=slow, adjust=False, min_periods=slow).mean()
    out["macd_line"] = out["macd_fast_ema"] - out["macd_slow_ema"]
    out["macd_signal_line"] = out["macd_line"].ewm(span=signal_span, adjust=False, min_periods=signal_span).mean()
    out["macd_histogram"] = out["macd_line"] - out["macd_signal_line"]
    out["macd_raw_signal"] = (out["macd_line"] > out["macd_signal_line"]).astype(float)
    out["macd_signal_executable"] = out["macd_raw_signal"].shift(1).fillna(0.0)
    out["macd_slope_executable"] = out["macd_line"].diff().shift(1).fillna(0.0)
    return out


def add_realized_risk_features(df: pd.DataFrame, realized_window: int, trend_window: int) -> pd.DataFrame:
    out = df.copy()
    out["realized_volatility"] = out["simple_return"].shift(1).rolling(realized_window, min_periods=5).std() * np.sqrt(TRADING_DAYS)
    previous_close = out["close"].shift(1)
    recent_high = previous_close.rolling(trend_window, min_periods=5).max()
    out["price_drawdown_recent_high"] = previous_close / recent_high - 1.0
    out["trend_strength"] = previous_close / previous_close.shift(trend_window) - 1.0
    return out
