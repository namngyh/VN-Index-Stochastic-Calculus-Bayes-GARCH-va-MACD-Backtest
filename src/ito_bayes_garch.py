from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from stochastic_ito_bayes_garch_strategy import (
    fit_garch,
    recursive_bayes_garch_forecast,
    sample_garch_posterior,
)


@dataclass(frozen=True)
class ItoForecastConfig:
    drift_window: int
    prior_strength: int
    posterior_samples: int
    random_state: int
    min_train_observations: int = 252


def walk_forward_yearly_forecasts(
    full_df: pd.DataFrame,
    start_date: pd.Timestamp,
    cfg: ItoForecastConfig,
) -> pd.DataFrame:
    records: list[pd.DataFrame] = []
    target_df = full_df[full_df["date"] >= start_date].copy()
    years = sorted(target_df["date"].dt.year.unique())

    for offset, year in enumerate(years):
        year_start = pd.Timestamp(year=year, month=1, day=1)
        fit_df = full_df[full_df["date"] < year_start].copy()
        target_year = full_df[(full_df["date"].dt.year == year) & (full_df["date"] >= start_date)].copy()
        if len(target_year) == 0 or len(fit_df) < cfg.min_train_observations:
            continue

        result = fit_garch(fit_df["log_return"])
        posterior = sample_garch_posterior(
            result,
            samples=cfg.posterior_samples,
            random_state=cfg.random_state + offset * 17,
        )
        forecast = recursive_bayes_garch_forecast(
            result=result,
            posterior=posterior,
            full_returns=full_df["log_return"],
            test_index=target_year.index,
            drift_prior_mean=float(fit_df["log_return"].mean()),
            drift_prior_strength=cfg.prior_strength,
            drift_window=cfg.drift_window,
            random_state=cfg.random_state + offset * 17 + 1,
        )
        forecast["forecast_fit_start"] = fit_df["date"].iloc[0]
        forecast["forecast_fit_end"] = fit_df["date"].iloc[-1]
        forecast["forecast_year"] = year
        records.append(forecast)

    if not records:
        raise ValueError("No walk-forward forecast blocks were produced.")
    return pd.concat(records, axis=0).sort_index()
