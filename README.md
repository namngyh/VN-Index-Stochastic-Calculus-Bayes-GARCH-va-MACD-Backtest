# VN-Index Stochastic Calculus, Bayes-GARCH và MACD Backtest

Repo này kiểm định chiến lược ra/vào lệnh VN-Index dựa trên Stochastic Calculus, bổ đề Ito, chuyển động Brown, Bayes-GARCH và so sánh với thuật toán MACD(12,26,9) trong điều kiện chỉ `long` hoặc `exit/cash`.

## Nội dung chính

- `stochastic_ito_bayes_garch_strategy.py`: pipeline đọc dữ liệu, fit Ito Bayes-GARCH, tạo tín hiệu MACD, backtest và sinh báo cáo.
- `optimize_strategy_parameters.py`: tối ưu tham số trên validation, sau đó đánh giá out-of-sample trên test.
- `VN_Index_Stochastic_MACD_Backtest.ipynb`: notebook trực quan hóa, nhận xét học thuật, đo lường rủi ro và so sánh mô hình.
- `READ.md`: báo cáo Markdown chính với bảng so sánh, total điểm, annual return, rủi ro nâng cao và thống kê lệnh.
- `outputs_stochastic_calculus/`: toàn bộ CSV, PNG, báo cáo và bảng backtest.
- `outputs_optimization/`: kết quả grid search, bảng tham số tối ưu, backtest test cuối và biểu đồ equity curve tối ưu.

## Chạy lại

```bash
/home/namngyh/miniconda3/envs/eda/bin/python stochastic_ito_bayes_garch_strategy.py
```

Chạy tối ưu tham số:

```bash
/home/namngyh/miniconda3/envs/eda/bin/python optimize_strategy_parameters.py
```

## Kết quả test nổi bật

| Strategy | Total points | Total return | CAGR | Sharpe | Max drawdown |
|---|---:|---:|---:|---:|---:|
| Ito Bayes-GARCH | 379.70 | 30.75% | 4.51% | 0.373 | -20.32% |
| MACD(12,26,9) | 840.55 | 88.10% | 10.95% | 0.939 | -25.18% |
| Buy & Hold | 1,031.16 | 123.61% | 14.15% | 0.768 | -40.34% |

## Kết quả tối ưu tham số

Optimizer dùng split `60% train / 20% validation / 20% test`. Tham số được chọn trên validation, test cuối không dùng để chọn tham số.

| Strategy | Best params | Test total return | Test CAGR | Test Sharpe | Test max drawdown |
|---|---|---:|---:|---:|---:|
| Baseline Ito | drift 63, prior 126, risk buffer 0.02 | 1.29% | 0.32% | 0.091 | -18.48% |
| Optimized Ito | drift 21, prior 63, risk buffer 0.04 | 15.69% | 3.66% | 0.371 | -18.88% |
| Baseline MACD | MACD(12,26,9) | 48.80% | 10.31% | 0.885 | -21.39% |
| Optimized MACD | MACD(6,26,12) | 66.48% | 13.41% | 1.111 | -21.27% |

## Biểu đồ chính

- `outputs_stochastic_calculus/forecast_train_test.png`
- `outputs_stochastic_calculus/backtest_equity_curve.png`
- `outputs_stochastic_calculus/macd_indicator_test.png`
- `outputs_stochastic_calculus/macd_signals_on_price.png`
- `outputs_stochastic_calculus/drawdown_comparison_test.png`
- `outputs_stochastic_calculus/rolling_volatility_comparison_test.png`
- `outputs_stochastic_calculus/return_distribution_test.png`
- `outputs_optimization/optimized_equity_curve_test.png`
- `outputs_optimization/ito_top_validation_scores.png`
- `outputs_optimization/macd_top_validation_scores.png`

Đây là research backtest, không phải khuyến nghị đầu tư hay hệ thống giao dịch thực chiến.
