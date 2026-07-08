# VN-Index Stochastic Calculus, Bayes-GARCH và MACD Backtest

Repo này kiểm định chiến lược ra/vào lệnh VN-Index dựa trên Stochastic Calculus, bổ đề Ito, chuyển động Brown, Bayes-GARCH và so sánh với thuật toán MACD tối ưu `MACD(6,26,12)` trong điều kiện chỉ `long` hoặc `exit/cash`.

## Nội dung chính

- `stochastic_ito_bayes_garch_strategy.py`: pipeline chính với tham số đã tối ưu.
- `optimize_strategy_parameters.py`: tối ưu tham số trên validation, sau đó đánh giá out-of-sample trên test.
- `stress_year_backtest.py`: stress-test 3 chiến lược trong các năm VN-Index biến động khó khăn nhất.
- `VN_Index_Stochastic_MACD_Backtest.ipynb`: notebook trực quan hóa, nhận xét chi tiết và so sánh mô hình.
- `READ.md`: báo cáo Markdown chi tiết với total điểm, annual return, rủi ro nâng cao và thống kê lệnh.
- `outputs_stochastic_calculus/`: CSV, PNG, report và bảng backtest sau khi cập nhật tham số tối ưu.
- `outputs_optimization/`: kết quả grid search, bảng tham số tối ưu và backtest test cuối.
- `outputs_stress_years/`: bảng, hình ảnh và báo cáo stress-test theo từng năm biến động mạnh.

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

Chạy stress-test các năm biến động mạnh:

```bash
/home/namngyh/miniconda3/envs/eda/bin/python stress_year_backtest.py
```

## Kết quả test nổi bật sau cập nhật

Khung thời gian test: `2020-05-14` đến `2026-07-01` (`1,532` phiên giao dịch).

| Strategy | Total points | Total return | CAGR | Sharpe | Max drawdown |
|---|---:|---:|---:|---:|---:|
| Ito Bayes-GARCH | 274.26 | 30.08% | 4.42% | 0.489 | -13.99% |
| MACD(6,26,12) | 1,101.27 | 130.15% | 14.70% | 1.223 | -21.27% |
| Buy & Hold | 1,031.16 | 123.61% | 14.15% | 0.768 | -40.34% |

## Stress-Test Các Năm Biến Động Mạnh

Stress-test chọn năm dựa trên composite stress score của VN-Index: annual volatility cao, downside volatility cao, max drawdown sâu và annual return yếu. 5 năm được chọn tự động là `2008`, `2022`, `2020`, `2018`, `2006`.

| Year | VN-Index return | Annual volatility | Max drawdown | Worst day | Stress score |
|---|---:|---:|---:|---:|---:|
| 2008 | -65.96% | 37.05% | -68.85% | -4.69% | 7 |
| 2022 | -32.78% | 24.83% | -40.34% | -4.95% | 16 |
| 2020 | 14.87% | 22.79% | -33.51% | -6.28% | 24 |
| 2018 | -9.32% | 22.28% | -26.21% | -5.10% | 26 |
| 2006 | 144.48% | 32.27% | -36.81% | -4.84% | 29 |

| Year | Best total return | Best drawdown control | Main observation |
|---|---|---|---|
| 2008 | Ito Bayes-GARCH `0.00%` | Ito Bayes-GARCH `0.00%` | Ito đứng ngoài hoàn toàn nên tránh được thị trường giảm sâu; MACD vẫn lỗ `-11.96%`; Buy & Hold giảm `-65.96%`. |
| 2022 | Ito Bayes-GARCH `-7.92%` | Ito Bayes-GARCH `-7.92%` | Cả ba đều chịu áp lực; Ito giảm ít nhất nhờ exposure chỉ `7.63%`. |
| 2020 | MACD(6,26,12) `46.13%` | Ito Bayes-GARCH `-4.23%` | Năm có cú sốc và hồi phục nhanh; MACD bắt trend hồi phục tốt nhất. |
| 2018 | MACD(6,26,12) `18.71%` | MACD(6,26,12) `-8.52%` | MACD vượt cả return và drawdown; Buy & Hold âm `-9.32%`. |
| 2006 | Buy & Hold `144.48%` | MACD(6,26,12) `-13.69%` | Năm tăng rất mạnh nhưng rung lắc lớn; Buy & Hold ăn trọn upside, MACD kiểm soát drawdown tốt hơn. |

![Stress-year ranking](outputs_stress_years/stress_year_ranking.png)

![Stress-year equity curves](outputs_stress_years/stress_year_equity_curves.png)

![Stress-year drawdowns](outputs_stress_years/stress_year_drawdowns.png)

![Stress-year metric heatmap](outputs_stress_years/stress_year_metric_heatmap.png)

Kết luận stress-test: Ito Bayes-GARCH là mô hình phòng thủ rõ rệt, đặc biệt trong năm giảm sâu như `2008` và `2022`; MACD(6,26,12) mạnh hơn khi thị trường có xu hướng hồi phục hoặc momentum rõ như `2020` và `2018`; Buy & Hold thắng trong năm tăng cực mạnh như `2006` nhưng phải chịu drawdown lớn.

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
- `outputs_stress_years/stress_year_ranking.png`
- `outputs_stress_years/stress_year_equity_curves.png`
- `outputs_stress_years/stress_year_drawdowns.png`
- `outputs_stress_years/stress_year_metric_heatmap.png`

Đây là research backtest, không phải khuyến nghị đầu tư hay hệ thống giao dịch thực chiến.
