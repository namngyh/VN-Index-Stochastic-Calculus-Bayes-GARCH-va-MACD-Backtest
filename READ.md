# VN-Index Stochastic Calculus, Bayes-GARCH va MACD Backtest

Project này kiểm định chiến lược ra/vào lệnh VN-Index dựa trên Stochastic Calculus và so sánh với thuật toán MACD(12,26,9).

- Ito Bayes-GARCH: dự báo drift/volatility từ `dS/S = mu dt + sigma dW` và bổ đề Ito `d log(S) = (mu - 0.5 sigma^2)dt + sigma dW`.
- MACD(12,26,9): `MACD line = EMA12 - EMA26`, `signal line = EMA9(MACD line)`.
- Điều kiện MACD: chỉ `long` khi MACD line lớn hơn signal line, ngược lại `exit/cash`.
- Tín hiệu MACD được dịch 1 phiên: tín hiệu sau khi đóng cửa hôm nay áp dụng cho lợi nhuận phiên kế tiếp.
- Buy & Hold: benchmark nắm giữ VN-Index liên tục.

## Cách chạy lại

```bash
/home/namngyh/miniconda3/envs/eda/bin/python stochastic_ito_bayes_garch_strategy.py
```

Kết quả được lưu trong `outputs_stochastic_calculus/`.

Notebook trực quan chính:

- `VN_Index_Stochastic_MACD_Backtest.ipynb`: notebook trình bày mô hình, biểu đồ, bảng đo lường và nhận xét học thuật.

## Chia dữ liệu

- Full data dùng cho backtest: `2006-01-03` đến `2026-07-01`, gồm `5,104` quan sát daily return.
- Train: `2006-01-03` đến `2020-05-13`, gồm `3,572` quan sát.
- Test: `2020-05-14` đến `2026-07-01`, gồm `1,532` quan sát.

## Bảng So Sánh Chính

| Metric | Full Data - Ito | Full Data - MACD(12,26,9) | Full Data - Buy & Hold | Test - Ito | Test - MACD(12,26,9) | Test - Buy & Hold |
|---|---:|---:|---:|---:|---:|---:|
| Market exposure | 57.03% | 53.10% | 100.00% | 66.32% | 54.90% | 100.00% |
| Total VN-Index points | 1,348.26 | 2,489.23 | 1,557.87 | 379.70 | 840.55 | 1,031.16 |
| Annual VN-Index points | 66.57 | 122.90 | 76.92 | 62.46 | 138.26 | 169.62 |
| Total return | 670.74% | 3219.12% | 506.62% | 30.75% | 88.10% | 123.61% |
| CAGR | 10.61% | 18.88% | 9.31% | 4.51% | 10.95% | 14.15% |
| Annualized mean return | 11.32% | 18.31% | 11.40% | 5.51% | 11.10% | 15.21% |
| Annual volatility | 15.67% | 14.22% | 22.33% | 14.76% | 11.82% | 19.81% |
| Downside volatility | 15.80% | 13.76% | 17.03% | 16.21% | 13.23% | 17.27% |
| Sharpe ratio | 0.722 | 1.287 | 0.511 | 0.373 | 0.939 | 0.768 |
| Sortino ratio | 0.716 | 1.331 | 0.670 | 0.340 | 0.839 | 0.881 |
| Calmar ratio | 0.251 | 0.507 | 0.117 | 0.222 | 0.435 | 0.351 |
| Max drawdown | -42.24% | -37.21% | -79.88% | -20.32% | -25.18% | -40.34% |
| Average drawdown | -15.08% | -6.94% | -35.66% | -9.70% | -7.70% | -14.22% |
| Ulcer index | 17.01% | 8.99% | 41.08% | 10.63% | 8.92% | 16.85% |
| Daily VaR 95% | -1.47% | -1.28% | -2.42% | -1.44% | -1.06% | -2.00% |
| Daily CVaR 95% | -2.60% | -2.21% | -3.51% | -2.68% | -2.01% | -3.40% |
| Daily VaR 99% | -3.42% | -2.85% | -4.22% | -3.40% | -2.68% | -4.17% |
| Daily CVaR 99% | -4.29% | -3.67% | -4.85% | -4.73% | -3.75% | -5.19% |
| Profit factor | 1.188 | 1.369 | 1.095 | 1.087 | 1.253 | 1.152 |
| Beta to buy-and-hold | 0.493 | 0.407 |  | 0.554 | 0.355 |  |
| Annual alpha | 5.70% | 13.67% |  | -2.92% | 5.69% |  |
| Tracking error | 15.90% | 17.17% |  | 13.23% | 15.91% |  |
| Information ratio | -0.005 | 0.402 |  | -0.733 | -0.259 |  |
| Up capture | 54.34% | 51.54% |  | 59.05% | 47.22% |  |
| Down capture | 50.07% | 41.18% |  | 62.51% | 43.32% |  |
| Trades | 116.0 | 166.0 |  | 49.0 | 57.0 |  |
| Trade win rate | 39.66% | 50.60% |  | 46.94% | 49.12% |  |
| Average trade return | 2.48% | 2.44% |  | 0.76% | 1.22% |  |
| Median trade return | -0.50% | 0.01% |  | -0.20% | -0.32% |  |
| Best trade | 88.38% | 56.72% |  | 37.92% | 18.66% |  |
| Worst trade | -12.84% | -11.73% |  | -12.84% | -7.95% |  |
| Average holding days | 26.1 | 17.3 |  | 21.7 | 15.7 |  |
| Median holding days | 8.0 | 15.0 |  | 10.0 | 15.0 |  |
| Expectancy per trade | 2.48% | 2.44% |  | 0.76% | 1.22% |  |
| Average trade points | 11.62 | 15.00 |  | 7.75 | 14.75 |  |
| Median trade points | -3.06 | 0.14 |  | -2.12 | -4.48 |  |
| Best trade points | 454.34 | 236.65 |  | 337.44 | 236.65 |  |
| Worst trade points | -117.49 | -98.97 |  | -115.59 | -81.76 |  |

## Nhận Xét Nhanh

- Trên full data, MACD(12,26,9) vượt cả Ito và Buy & Hold: total return `3219.12%`, CAGR `18.88%`, Sharpe `1.287`.
- Trên test, MACD đạt `88.10%`, thấp hơn Buy & Hold `123.61%` nhưng cao hơn Ito `30.75%`.
- MACD có rủi ro test tốt hơn Buy & Hold: annual volatility `11.82%` so với `19.81%`, VaR 95% `-1.06%` so với `-2.00%`.
- Ito có max drawdown test thấp nhất trong 3 nhóm: `-20.32%`, nhưng lợi nhuận thấp hơn.
- MACD có beta thấp nhất với thị trường: `0.407` full data và `0.355` test, thể hiện mức tiếp xúc thị trường thấp hơn.
- Theo tổng điểm VN-Index, MACD tốt hơn Ito trên cả full data và test, nhưng trên test vẫn thấp hơn Buy & Hold về điểm tuyệt đối.

## File Output Quan Trọng

- `outputs_stochastic_calculus/advanced_backtest_metrics.md`: bảng đầy đủ tất cả chỉ số.
- `outputs_stochastic_calculus/advanced_backtest_metrics.csv`: bảng raw numeric.
- `outputs_stochastic_calculus/advanced_backtest_metrics_formatted.csv`: bảng đã format.
- `outputs_stochastic_calculus/full_data_backtest.csv`: backtest Ito full data.
- `outputs_stochastic_calculus/strategy_backtest.csv`: backtest Ito test set.
- `outputs_stochastic_calculus/macd_full_data_backtest.csv`: backtest MACD full data.
- `outputs_stochastic_calculus/macd_strategy_backtest.csv`: backtest MACD test set.
- `outputs_stochastic_calculus/backtest_equity_curve.png`: equity curve test gồm Ito, MACD và Buy & Hold.
- `outputs_stochastic_calculus/macd_indicator_test.png`: MACD line, signal line và histogram.
- `outputs_stochastic_calculus/macd_signals_on_price.png`: điểm long/exit của MACD trên giá.
- `outputs_stochastic_calculus/drawdown_comparison_test.png`: so sánh drawdown Ito, MACD và Buy & Hold.
- `outputs_stochastic_calculus/rolling_volatility_comparison_test.png`: rolling volatility 63 phiên.
- `outputs_stochastic_calculus/return_distribution_test.png`: phân phối daily return.
- `outputs_stochastic_calculus/signals_on_price.png`: điểm vào/ra lệnh Ito.
- `outputs_stochastic_calculus/forecast_train_test.png`: biểu đồ forecast train/test.
