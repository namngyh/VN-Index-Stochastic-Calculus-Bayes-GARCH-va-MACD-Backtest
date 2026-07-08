# Strategy Parameter Optimization Report

## Method

- Split: train / validation / test = `60%` / `20%` / `20%`.
- Train: `2006-01-03` to `2018-04-26`.
- Validation: `2018-04-27` to `2022-05-27`.
- Test: `2022-05-30` to `2026-07-01`.
- Selection objective: validation `Sharpe + 0.30 * Calmar + 0.20 * CAGR`, with penalties for too few trades or extreme exposure.
- Final test is not used for parameter selection.

## Best Validation Parameters

### Ito Bayes-GARCH

- `drift_window`: `21`
- `prior_strength`: `63`
- `risk_buffer`: `0.0400`
- validation score: `1.107`

### MACD

- `fast`: `6`
- `slow`: `26`
- `signal_span`: `12`
- validation score: `1.603`

## Final Test Comparison

| strategy       | total_points | annual_points | total_return | cagr   | annual_volatility | sharpe | sortino | calmar | max_drawdown | var_95_daily | cvar_95_daily | trades | trade_win_rate | avg_trade_return | avg_trade_points | exposure | score  |
| -------------- | ------------ | ------------- | ------------ | ------ | ----------------- | ------ | ------- | ------ | ------------ | ------------ | ------------- | ------ | -------------- | ---------------- | ---------------- | -------- | ------ |
| Baseline Ito   | 40.18        | 9.92          | 1.29%        | 0.32%  | 13.37%            | 0.091  | 0.084   | 0.017  | -18.48%      | -1.30%       | -2.37%        | 32     | 31.25%         | 0.13%            | 1.26             | 66.01%   | 0.097  |
| Optimized Ito  | 253.11       | 62.47         | 15.69%       | 3.66%  | 11.51%            | 0.371  | 0.292   | 0.194  | -18.88%      | -0.99%       | -2.05%        | 48     | 39.58%         | 0.40%            | 5.27             | 50.15%   | 0.436  |
| Baseline MACD  | 618.84       | 152.74        | 48.80%       | 10.31% | 11.88%            | 0.885  | 0.800   | 0.482  | -21.39%      | -1.07%       | -1.99%        | 36     | 52.78%         | 1.23%            | 17.19            | 54.55%   | 1.051  |
| Optimized MACD | 772.12       | 190.57        | 66.48%       | 13.41% | 11.97%            | 1.111  | 1.000   | 0.630  | -21.27%      | -1.02%       | -2.01%        | 40     | 52.50%         | 1.39%            | 19.30            | 54.95%   | 1.327  |
| Buy & Hold     | 579.28       | 142.98        | 45.04%       | 9.61%  | 19.25%            | 0.574  | 0.678   | 0.317  | -30.28%      | -1.86%       | -3.20%        | 1      | 100.00%        | 45.04%           | 579.28           | 100.00%  | -0.812 |

## Academic Reading

The optimized MACD configuration is selected as a trend-following rule, while the Ito Bayes-GARCH configuration is selected as a stochastic drift-volatility filter. A higher validation score does not guarantee dominance on the test set; it only formalizes the parameter search without looking at future test outcomes. The gap between validation and test performance should be read as model-selection risk.
