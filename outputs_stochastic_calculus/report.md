# VN-Index Stochastic Calculus Strategy Report

## Model

- Price process: `dS/S = mu dt + sigma dW`, with Brownian motion `W_t`.
- Ito lemma: `d log(S) = (mu - 0.5 sigma^2)dt + sigma dW`.
- Return engine: Student-t GARCH(1,1), then an approximate Bayesian posterior around the fitted parameters.
- Drift forecast: Bayesian rolling mean over `63` sessions, shrunk toward the train-set prior with strength `126`.
- Signal: long VN-Index when forecast log-return is greater than `0.02` times forecast daily volatility; otherwise cash.
- Transaction cost assumption: `0.05%` per position change.

## Data Split

- Data file: `data.csv`
- Clean sample: `5,104` daily returns from `2006-01-03` to `2026-07-01`
- Modeling start date: `2006-01-01`
- Train: `3,572` rows from `2006-01-03` to `2020-05-13`
- Test: `1,532` rows from `2020-05-14` to `2026-07-01`

## Fitted Bayes-GARCH Center

- mu: `0.065930` percent daily
- omega: `0.028805`
- alpha[1]: `0.162923`
- beta[1]: `0.834932`
- nu: `9.567`

## Forecast Quality on Test

- RMSE close: `16.096`
- MAE close: `10.885`
- R2 close: `0.9959`
- Directional accuracy: `55.22%`
- Mean forecast daily log-return: `0.04%`
- Mean actual daily log-return: `0.05%`
- Mean forecast daily volatility: `1.19%`

## Backtest on Test

| Metric | Ito Bayes-GARCH Strategy | MACD(12,26,9) Long/Exit | Buy & Hold |
|---|---:|---:|---:|
| Total return | 30.75% | 88.10% | 123.61% |
| CAGR | 4.51% | 10.95% | 14.15% |
| Annual volatility | 14.76% | 11.82% | 19.81% |
| Sharpe | 0.373 | 0.939 | 0.768 |
| Max drawdown | -20.32% | -25.18% | -40.34% |
| Win rate | 37.66% | 31.72% | 57.18% |

## Files

- `predictions.csv`: train/test forecasts and predictive bands.
- `strategy_backtest.csv`: test-set signals, returns, and equity curves.
- `full_data_backtest.csv`: full-sample signals, returns, and equity curves.
- `macd_strategy_backtest.csv`: test-set MACD(12,26,9) long/exit signals and equity curve.
- `macd_full_data_backtest.csv`: full-sample MACD(12,26,9) long/exit backtest.
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
