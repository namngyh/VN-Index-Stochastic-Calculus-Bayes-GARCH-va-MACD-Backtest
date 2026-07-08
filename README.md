# VN-Index Stochastic Calculus, Bayes-GARCH và MACD Backtest

Repo này kiểm định chiến lược ra/vào lệnh VN-Index dựa trên Stochastic Calculus, bổ đề Ito, chuyển động Brown, Bayes-GARCH và so sánh với thuật toán MACD tối ưu `MACD(6,26,12)` trong điều kiện chỉ `long` hoặc `exit/cash`.

## Nội dung chính

- `stochastic_ito_bayes_garch_strategy.py`: pipeline chính với tham số đã tối ưu.
- `optimize_strategy_parameters.py`: tối ưu tham số trên validation, sau đó đánh giá out-of-sample trên test.
- `VN_Index_Stochastic_MACD_Backtest.ipynb`: notebook trực quan hóa, nhận xét chi tiết và so sánh mô hình.
- `READ.md`: báo cáo Markdown chi tiết với total điểm, annual return, rủi ro nâng cao và thống kê lệnh.
- `outputs_stochastic_calculus/`: CSV, PNG, report và bảng backtest sau khi cập nhật tham số tối ưu.
- `outputs_optimization/`: kết quả grid search, bảng tham số tối ưu và backtest test cuối.

## Tham số đang chốt trong pipeline chính

| Model | Parameters |
|---|---|
| Ito Bayes-GARCH | `drift_window=126`, `prior_strength=63`, `risk_buffer=0.08` |
| MACD | `fast=6`, `slow=26`, `signal=12` |

## Chạy lại

```bash
/home/namngyh/miniconda3/envs/eda/bin/python stochastic_ito_bayes_garch_strategy.py
```

Chạy tối ưu tham số:

```bash
/home/namngyh/miniconda3/envs/eda/bin/python optimize_strategy_parameters.py
```

## Kết quả test nổi bật sau cập nhật

Khung thời gian test: `2020-05-14` đến `2026-07-01` (`1,532` phiên giao dịch).

| Strategy | Total points | Total return | CAGR | Sharpe | Max drawdown |
|---|---:|---:|---:|---:|---:|
| Ito Bayes-GARCH | 274.26 | 30.08% | 4.42% | 0.489 | -13.99% |
| MACD(6,26,12) | 1,101.27 | 130.15% | 14.70% | 1.223 | -21.27% |
| Buy & Hold | 1,031.16 | 123.61% | 14.15% | 0.768 | -40.34% |

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
