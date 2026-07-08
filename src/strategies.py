from __future__ import annotations

import pandas as pd

from .risk_governor import build_full_defensive_position


def build_strategy_positions(
    frame: pd.DataFrame,
    components: pd.DataFrame,
    risk_cfg: dict,
    transaction_cost: float,
) -> tuple[dict[str, pd.Series], pd.DataFrame]:
    macd_signal = frame["macd_signal_executable"].fillna(0.0).astype(float)
    ito_signal = (frame["forecast_log_return"] > float(risk_cfg.get("ito_risk_buffer", 0.08)) * frame["forecast_volatility"]).astype(float)

    positions: dict[str, pd.Series] = {
        "Buy & Hold": pd.Series(1.0, index=frame.index),
        "MACD only": macd_signal,
        "Ito-Bayes-GARCH only": ito_signal,
        "MACD + Ito hard gate": macd_signal * ito_signal,
        "MACD + volatility targeting": macd_signal * components["volatility_scale"],
        "MACD + tail-risk gate": macd_signal * components["tail_risk_gate"],
    }
    full_position, diagnostics = build_full_defensive_position(
        frame=frame,
        macd_signal=macd_signal,
        components=components,
        cfg=risk_cfg,
        transaction_cost=transaction_cost,
    )
    positions["MACD + full defensive exposure"] = full_position
    return positions, diagnostics
