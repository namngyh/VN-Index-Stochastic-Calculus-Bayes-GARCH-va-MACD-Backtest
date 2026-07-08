# Hybrid Defensive Exposure Model Report

## Executive Summary

Mô hình đề xuất là một white-box hybrid trading framework. MACD đóng vai trò tạo tín hiệu alpha theo xu hướng, trong khi Ito-Bayes-GARCH Defensive Exposure Model đóng vai trò kiểm soát rủi ro thông qua dự báo volatility, Bayesian drift shrinkage, tail-risk-aware exposure adjustment và profit protection. Dù các tham số GARCH được ước lượng thống kê, cơ chế ra quyết định vẫn minh bạch và có thể giải thích về mặt kinh tế.

Full defensive exposure model có max drawdown `-14.72%` so với constraint `-15.00%`. So với MACD only, hybrid hy sinh `5758.41%` total return nếu số này dương, và cải thiện drawdown `18.41%` nếu số này dương.

## Current Model Review

Baseline hiện tại cho thấy MACD có raw return mạnh hơn Ito-Bayes-GARCH standalone, nhưng Ito kiểm soát drawdown và stress-period exposure tốt hơn. Vì vậy, phiên bản này không ép Ito thành alpha generator độc lập mà chuyển nó thành risk governor.

## Why MACD Should Be The Alpha Engine

MACD trả lời câu hỏi: có directional alpha/trend signal đáng giao dịch không? Trong dữ liệu hiện tại, MACD(6,26,12) phản ứng tốt với trend recovery và giữ raw return cao hơn Ito standalone.

## Why Ito-Bayes-GARCH Should Be The Defensive Exposure Model

Ito-Bayes-GARCH không nên được xem là một standalone alpha generator. Đóng góp chính của nó là cải thiện robustness của một chiến lược alpha có hướng bằng cách kiểm soát exposure dưới điều kiện stochastic volatility và Bayesian tail-risk uncertainty.

## Hybrid Model Architecture

Công thức lõi:

`position_t = MACD_signal_t * risk_allocation_t`

Full defensive exposure model:

`position_t = MACD_signal_t * volatility_scale_t * uncertainty_penalty_t * profit_protection_t`

và hard exit:

`if forecast_return_p05_t < loss_floor: position_t = 0`

Uncertainty proxy dùng trong bản này là độ rộng predictive interval chuẩn hóa: `(forecast_p95 - forecast_p05) / (3.29 * forecast_volatility) - 1`, sau đó clip về không nếu interval không rộng bất thường. Regime detection là report-only diagnostic, chưa trực tiếp điều khiển position.

## Strategy Variants

- Buy & Hold.
- MACD only.
- Ito-Bayes-GARCH only.
- MACD + Ito hard gate.
- MACD + volatility targeting.
- MACD + tail-risk gate.
- MACD + full defensive exposure model.

## Backtest Methodology

- VN-Index only.
- Long/cash only, no short-selling.
- Transaction cost: `0.05%` per position change.
- Walk-forward yearly Ito-Bayes-GARCH forecast: mỗi năm chỉ fit bằng dữ liệu trước năm đó.
- MACD signal được shift 1 phiên để tránh look-ahead bias.
- Fractional position nằm trong `[0, 1]`.

## Performance Comparison

| strategy                       | total_return | cagr   | annualized_volatility | sharpe_ratio | sortino_ratio | calmar_ratio | max_drawdown | cvar_95_daily | worst_month | worst_year | number_of_trades | exposure_ratio | return_per_unit_drawdown |
| ------------------------------ | ------------ | ------ | --------------------- | ------------ | ------------- | ------------ | ------------ | ------------- | ----------- | ---------- | ---------------- | -------------- | ------------------------ |
| Buy & Hold                     | 506.32%      | 9.31%  | 22.33%                | 0.511        | 0.670         | 0.116        | -79.88%      | -3.51%        | -24.90%     | -65.96%    | 1.00             | 100.00%        | 6.338                    |
| MACD only                      | 5956.38%     | 22.46% | 14.28%                | 1.490        | 1.562         | 0.678        | -33.13%      | -2.19%        | -12.98%     | -11.96%    | 192.00           | 54.11%         | 179.794                  |
| Ito-Bayes-GARCH only           | 259.32%      | 6.52%  | 12.08%                | 0.583        | 0.442         | 0.173        | -37.58%      | -2.05%        | -16.93%     | -7.81%     | 133.00           | 32.37%         | 6.900                    |
| MACD + Ito hard gate           | 452.55%      | 8.81%  | 8.34%                 | 1.053        | 0.661         | 0.508        | -17.33%      | -1.18%        | -6.20%      | -6.90%     | 127.00           | 19.20%         | 26.121                   |
| MACD + volatility targeting    | 936.60%      | 12.24% | 8.78%                 | 1.359        | 1.387         | 0.625        | -19.57%      | -1.37%        | -4.89%      | -6.39%     | 192.00           | 40.29%         | 47.851                   |
| MACD + tail-risk gate          | 352.52%      | 7.74%  | 9.03%                 | 0.871        | 0.741         | 0.397        | -19.49%      | -1.49%        | -5.38%      | -7.56%     | 241.00           | 38.28%         | 18.083                   |
| MACD + full defensive exposure | 197.97%      | 5.54%  | 6.86%                 | 0.821        | 0.690         | 0.376        | -14.72%      | -1.13%        | -3.74%      | -5.09%     | 241.00           | 29.78%         | 13.451                   |

## Risk-Adjusted Performance

Calmar, Sortino, CVaR, time-under-water và return per unit drawdown là trọng tâm chính. Objective nghiên cứu không phải raw return đơn thuần mà là cân bằng giữa lợi nhuận, drawdown và turnover.

## Stress-Test Analysis

Stress years used: `2008, 2020, 2022, 2018, 2006`.

| year | strategy                       | total_return | calmar_ratio | sortino_ratio | max_drawdown | cvar_95_daily | exposure_ratio |
| ---- | ------------------------------ | ------------ | ------------ | ------------- | ------------ | ------------- | -------------- |
| 2006 | Buy & Hold                     | 144.35%      | 3.993        | 4.545         | -36.81%      | -4.15%        | 100.00%        |
| 2008 | Buy & Hold                     | -65.96%      | -0.973       | -5.134        | -68.85%      | -4.47%        | 100.00%        |
| 2018 | Buy & Hold                     | -9.32%       | -0.361       | -0.428        | -26.21%      | -3.52%        | 100.00%        |
| 2020 | Buy & Hold                     | 14.87%       | 0.444        | 0.736         | -33.51%      | -4.16%        | 100.00%        |
| 2022 | Buy & Hold                     | -32.78%      | -0.821       | -1.914        | -40.34%      | -4.06%        | 100.00%        |
| 2006 | MACD only                      | 184.06%      | 13.703       | 5.694         | -13.69%      | -3.07%        | 59.04%         |
| 2008 | MACD only                      | -11.96%      | -0.429       | -0.509        | -28.59%      | -3.64%        | 48.98%         |
| 2018 | MACD only                      | 18.71%       | 2.235        | 1.434         | -8.52%       | -2.08%        | 59.27%         |
| 2020 | MACD only                      | 46.13%       | 5.030        | 2.801         | -9.17%       | -2.02%        | 61.11%         |
| 2022 | MACD only                      | -9.16%       | -0.435       | -0.514        | -21.27%      | -2.74%        | 50.60%         |
| 2006 | Ito-Bayes-GARCH only           | 61.18%       | 1.653        | 2.346         | -37.58%      | -4.05%        | 70.28%         |
| 2008 | Ito-Bayes-GARCH only           | 0.00%        |              |               | 0.00%        | 0.00%         | 0.00%          |
| 2018 | Ito-Bayes-GARCH only           | 2.03%        | 0.144        | 0.125         | -14.36%      | -2.23%        | 26.21%         |
| 2020 | Ito-Bayes-GARCH only           | 19.10%       | 4.352        | 1.791         | -4.39%       | -1.00%        | 30.16%         |
| 2022 | Ito-Bayes-GARCH only           | -7.81%       | -0.835       | -0.703        | -9.45%       | -1.13%        | 10.44%         |
| 2006 | MACD + Ito hard gate           | 107.33%      | 8.391        | 3.914         | -13.01%      | -2.77%        | 43.78%         |
| 2008 | MACD + Ito hard gate           | 0.00%        |              |               | 0.00%        | 0.00%         | 0.00%          |
| 2018 | MACD + Ito hard gate           | 15.56%       | 5.849        | 1.129         | -2.71%       | -0.80%        | 20.56%         |
| 2020 | MACD + Ito hard gate           | 11.04%       | 6.130        | 1.372         | -1.80%       | -0.75%        | 19.05%         |
| 2022 | MACD + Ito hard gate           | -2.66%       | -0.612       | -0.304        | -4.41%       | -0.47%        | 6.02%          |
| 2006 | MACD + volatility targeting    | 58.37%       | 8.314        | 5.504         | -7.13%       | -1.41%        | 31.69%         |
| 2008 | MACD + volatility targeting    | -6.39%       | -0.427       | -0.780        | -15.39%      | -1.47%        | 23.08%         |
| 2018 | MACD + volatility targeting    | 13.24%       | 2.528        | 1.460         | -5.33%       | -1.45%        | 44.60%         |
| 2020 | MACD + volatility targeting    | 23.84%       | 3.000        | 1.849         | -7.95%       | -1.66%        | 46.74%         |
| 2022 | MACD + volatility targeting    | -6.37%       | -0.560       | -0.681        | -11.52%      | -1.54%        | 32.66%         |
| 2006 | MACD + tail-risk gate          | 20.00%       | 4.135        | 1.767         | -4.90%       | -1.27%        | 22.49%         |
| 2008 | MACD + tail-risk gate          | -5.92%       | -0.720       | -0.645        | -8.45%       | -0.93%        | 7.76%          |
| 2018 | MACD + tail-risk gate          | 7.04%        | 1.002        | 0.631         | -7.14%       | -1.71%        | 43.55%         |
| 2020 | MACD + tail-risk gate          | 20.73%       | 2.985        | 1.523         | -6.94%       | -1.72%        | 46.03%         |
| 2022 | MACD + tail-risk gate          | 0.60%        | 0.107        | 0.096         | -5.64%       | -1.09%        | 25.30%         |
| 2006 | MACD + full defensive exposure | 14.39%       | 3.301        | 1.523         | -4.41%       | -1.08%        | 18.27%         |
| 2008 | MACD + full defensive exposure | -5.09%       | -0.851       | -0.706        | -6.15%       | -0.66%        | 4.89%          |
| 2018 | MACD + full defensive exposure | 8.17%        | 2.114        | 0.965         | -3.93%       | -1.31%        | 36.04%         |
| 2020 | MACD + full defensive exposure | 9.21%        | 1.842        | 0.860         | -5.00%       | -1.32%        | 30.07%         |
| 2022 | MACD + full defensive exposure | 0.35%        | 0.125        | 0.096         | -2.83%       | -0.55%        | 12.65%         |

## Regime Analysis

| regime        | observations | total_return | calmar_ratio | sortino_ratio | max_drawdown | exposure_ratio |
| ------------- | ------------ | ------------ | ------------ | ------------- | ------------ | -------------- |
| high_vol_chop | 70.00        | 11.24%       | 13.627       | 4.905         | -3.43%       | 41.03%         |
| panic         | 1,905.00     | -4.21%       | -0.096       | -0.143        | -5.93%       | 0.85%          |
| recovery      | 68.00        | -8.68%       | -3.123       | -3.745        | -9.15%       | 30.85%         |
| sideways      | 2,397.00     | 87.01%       | 0.490        | 0.822         | -13.89%      | 43.89%         |
| trend_up      | 664.00       | 63.74%       | 3.256        | 2.381         | -6.32%       | 60.55%         |

## Drawdown and Tail-Risk Analysis

Hybrid model dùng volatility targeting để giảm exposure mềm khi forecast volatility cao, tail-risk gate để exit cứng khi predictive p05 thấp hơn loss floor, uncertainty penalty để giảm vốn khi predictive interval rộng bất thường, và equity/profit protection để bảo vệ đường vốn khi drawdown hoặc volatility xấu đi.

## Interpretation

Nếu hybrid giảm max drawdown và cải thiện Calmar/Sortino so với MACD only, Ito-Bayes-GARCH layer đang tạo giá trị như một risk governor. Nếu hybrid làm mất quá nhiều return mà không cải thiện risk-adjusted metrics, risk governor đang quá bảo thủ hoặc target volatility/loss floor cần chỉnh lại trên validation.

## Limitations

- GARCH posterior vẫn là asymptotic approximation quanh MLE, chưa phải MCMC đầy đủ.
- Profit protection là path-dependent risk rule, cần stress-test thêm với phí và slippage.
- Regime detection hiện chỉ để giải thích, chưa tối ưu hoặc điều khiển position.
- Dữ liệu chỉ VN-Index, chưa mở rộng sang tài sản khác.

## Next Development Steps

1. Tối ưu target volatility, loss floor và uncertainty penalty trên validation, giữ test cuối độc lập.
2. Thử walk-forward refit theo quý hoặc tháng nếu laptop cho phép.
3. Kiểm định độ nhạy transaction cost.
4. Thử regime detection làm overlay nhẹ sau khi report-only diagnostic ổn định.
