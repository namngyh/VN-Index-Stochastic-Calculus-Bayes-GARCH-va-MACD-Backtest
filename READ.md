# VN-Index Stochastic Calculus, Bayes-GARCH va MACD Backtest

Project này kiểm định chiến lược ra/vào lệnh VN-Index dựa trên Stochastic Calculus và so sánh với thuật toán MACD tối ưu.

- Ito Bayes-GARCH: dự báo drift/volatility từ `dS/S = mu dt + sigma dW` và bổ đề Ito `d log(S) = (mu - 0.5 sigma^2)dt + sigma dW`.
- MACD tối ưu: `MACD(6,26,12)`, tức `MACD line = EMA6 - EMA26`, `signal line = EMA12(MACD line)`.
- Điều kiện giao dịch: chỉ `long` khi tín hiệu xác nhận, ngược lại `exit/cash`.
- Tín hiệu MACD được dịch 1 phiên để giảm look-ahead bias.
- Buy & Hold: benchmark nắm giữ VN-Index liên tục.

## Tham Số Đã Chốt

| Model | Parameters |
|---|---|
| Ito Bayes-GARCH | `drift_window=126`, `prior_strength=63`, `risk_buffer=0.08` |
| MACD | `fast=6`, `slow=26`, `signal=12` |

## Cách Chạy Lại

```bash
/home/namngyh/miniconda3/envs/eda/bin/python stochastic_ito_bayes_garch_strategy.py
```

Chạy tối ưu tham số:

```bash
/home/namngyh/miniconda3/envs/eda/bin/python optimize_strategy_parameters.py
```

Notebook trực quan chính:

- `VN_Index_Stochastic_MACD_Backtest.ipynb`

## Chia Dữ Liệu Pipeline Chính

- Full data dùng cho backtest: `2006-01-03` đến `2026-07-01`, gồm `5,104` quan sát daily return.
- Train: `2006-01-03` đến `2020-05-13`, gồm `3,572` quan sát.
- Test: `2020-05-14` đến `2026-07-01`, gồm `1,532` quan sát.

## Bảng So Sánh Sau Khi Cập Nhật Tham Số

Khung thời gian test trong bảng: `2020-05-14` đến `2026-07-01` (`1,532` phiên giao dịch).

| Metric | Full Data - Ito | Full Data - MACD(6,26,12) | Full Data - Buy & Hold | Test - Ito | Test - MACD(6,26,12) | Test - Buy & Hold |
|---|---:|---:|---:|---:|---:|---:|
| Market exposure | 27.02% | 53.59% | 100.00% | 33.16% | 55.16% | 100.00% |
| Total VN-Index points | 837.07 | 2,855.75 | 1,557.87 | 274.26 | 1,101.27 | 1,031.16 |
| Annual VN-Index points | 41.33 | 141.00 | 76.92 | 45.11 | 181.15 | 169.62 |
| Total return | 194.56% | 4431.92% | 506.62% | 30.08% | 130.15% | 123.61% |
| CAGR | 5.48% | 20.72% | 9.31% | 4.42% | 14.70% | 14.15% |
| Annualized mean return | 6.00% | 19.84% | 11.40% | 4.81% | 14.41% | 15.21% |
| Annual volatility | 11.55% | 14.15% | 22.33% | 9.84% | 11.79% | 19.81% |
| Downside volatility | 16.55% | 13.65% | 17.03% | 14.27% | 13.23% | 17.27% |
| Sharpe ratio | 0.520 | 1.402 | 0.511 | 0.489 | 1.223 | 0.768 |
| Sortino ratio | 0.363 | 1.454 | 0.670 | 0.337 | 1.090 | 0.881 |
| Calmar ratio | 0.157 | 0.625 | 0.117 | 0.316 | 0.691 | 0.351 |
| Max drawdown | -34.88% | -33.13% | -79.88% | -13.99% | -21.27% | -40.34% |
| Average drawdown | -14.08% | -5.40% | -35.66% | -7.61% | -4.77% | -14.22% |
| Ulcer index | 15.29% | 7.21% | 41.08% | 8.02% | 5.92% | 16.85% |
| Daily VaR 95% | -0.79% | -1.27% | -2.42% | -0.79% | -1.02% | -2.00% |
| Daily CVaR 95% | -1.95% | -2.19% | -3.51% | -1.76% | -1.99% | -3.40% |
| Daily VaR 99% | -2.74% | -2.85% | -4.22% | -2.54% | -2.67% | -4.17% |
| Daily CVaR 99% | -3.73% | -3.64% | -4.85% | -3.44% | -3.75% | -5.19% |
| Profit factor | 1.194 | 1.407 | 1.095 | 1.157 | 1.344 | 1.152 |
| Beta to buy-and-hold | 0.268 | 0.403 |  | 0.247 | 0.354 |  |
| Annual alpha | 2.95% | 15.24% |  | 1.06% | 9.02% |  |
| Tracking error | 19.11% | 17.22% |  | 17.20% | 15.92% |  |
| Information ratio | -0.283 | 0.490 |  | -0.605 | -0.050 |  |
| Up capture | 28.08% | 52.00% |  | 30.56% | 48.54% |  |
| Down capture | 25.74% | 40.41% |  | 30.40% | 41.53% |  |
| Trades | 102.0 | 192.0 |  | 48.0 | 64.0 |  |
| Trade win rate | 44.12% | 51.56% |  | 45.83% | 53.12% |  |
| Average trade return | 1.23% | 2.22% |  | 0.61% | 1.40% |  |
| Median trade return | -0.67% | 0.15% |  | -0.55% | 0.15% |  |
| Best trade | 35.07% | 39.82% |  | 14.13% | 14.07% |  |
| Worst trade | -6.90% | -12.98% |  | -4.83% | -7.95% |  |
| Average holding days | 14.5 | 15.2 |  | 11.6 | 14.2 |  |
| Median holding days | 5.5 | 13.0 |  | 6.0 | 13.5 |  |
| Expectancy per trade | 1.23% | 2.22% |  | 0.61% | 1.40% |  |
| Average trade points | 8.21 | 14.87 |  | 5.71 | 17.21 |  |
| Median trade points | -5.64 | 1.39 |  | -7.05 | 2.01 |  |
| Best trade points | 240.32 | 234.05 |  | 139.94 | 234.05 |  |
| Worst trade points | -81.04 | -85.46 |  | -81.04 | -81.76 |  |

## Nhận Xét Nhanh

- MACD(6,26,12) hiện là chiến lược mạnh nhất trên test: total return `130.15%`, cao hơn Buy & Hold `123.61%`.
- MACD(6,26,12) có Sharpe `1.223`, cao hơn Buy & Hold `0.768`, đồng thời annual volatility chỉ `11.79%` so với `19.81%`.
- Ito Bayes-GARCH sau tối ưu là mô hình phòng thủ: max drawdown test chỉ `-13.99%`, thấp nhất trong ba nhóm.
- Ito có beta test `0.247`, thể hiện mức phụ thuộc thị trường thấp, nhưng tổng lợi nhuận vẫn thấp hơn MACD và Buy & Hold.
- MACD(6,26,12) tạo `1,101.27` điểm trên test, vượt Buy & Hold `1,031.16` điểm.

## Vì Sao Ito Bayes-GARCH Kém Hơn MACD Và Buy & Hold?

### Nguyên Nhân

1. **Mục tiêu của Ito Bayes-GARCH thiên về kiểm soát rủi ro hơn là bắt xu hướng**

   Mô hình Ito Bayes-GARCH dùng drift và volatility để quyết định long/cash. Sau tối ưu, `risk_buffer=0.08` làm điều kiện vào lệnh bảo thủ hơn: drift kỳ vọng phải đủ lớn so với volatility mới được long. Vì vậy exposure trên test chỉ `33.16%`, thấp hơn rất nhiều so với Buy & Hold `100.00%` và thấp hơn MACD `55.16%`. Khi VN-Index tăng mạnh trong test, mô hình bỏ lỡ nhiều đoạn tăng.

2. **Drift trong mô hình stochastic rất nhỏ và nhiễu**

   Với chỉ số thị trường, thành phần drift hằng ngày thường nhỏ hơn volatility rất nhiều. Điều này khiến tín hiệu `forecast_log_return > risk_buffer * forecast_volatility` khó kích hoạt ổn định. Nói cách khác, mô hình bắt được rủi ro tốt hơn bắt được expected return.

3. **GARCH mạnh ở dự báo volatility, không nhất thiết mạnh ở dự báo hướng giá**

   Bayes-GARCH giúp mô hình nhận diện volatility clustering và tail risk, nhưng volatility forecast không đồng nghĩa với directional forecast. Kết quả directional accuracy quanh `54.90%` cho thấy tín hiệu hướng giá có tồn tại nhưng chưa đủ mạnh để tạo lợi nhuận vượt MACD.

4. **MACD phù hợp hơn với regime có động lượng**

   MACD(6,26,12) là bộ lọc trend-following. Trong giai đoạn test `2020-05-14` đến `2026-07-01`, VN-Index có các đoạn hồi phục và xu hướng rõ, nên MACD nắm bắt tốt hơn. MACD có exposure `55.16%`, trade win rate `53.12%`, average trade points `17.21`, đều tốt hơn Ito trên test.

5. **Ito bị trade-off giữa drawdown thấp và upside thấp**

   Ito có max drawdown test tốt nhất: `-13.99%`, thấp hơn MACD `-21.27%` và Buy & Hold `-40.34%`. Nhưng cái giá phải trả là total return chỉ `30.08%`, thấp hơn MACD `130.15%` và Buy & Hold `123.61%`.

6. **Giả định log-return kiểu Brownian/GARCH chưa mô tả đầy đủ cấu trúc thị trường**

   VN-Index chịu ảnh hưởng của dòng tiền, chính sách, tâm lý, thanh khoản và regime vĩ mô. Mô hình Ito-Bayes-GARCH hiện tại chủ yếu dùng chuỗi giá/return và volatility, nên chưa có thông tin trend, momentum, volume, macro hoặc regime filter. Vì vậy mô hình có nền tảng học thuật tốt nhưng chưa đủ thông tin để cạnh tranh với một rule momentum đơn giản trong giai đoạn thị trường có xu hướng.

### Hệ Quả

- Ito Bayes-GARCH phù hợp hơn như một **risk filter** hoặc **volatility-aware allocation model** thay vì một chiến lược alpha độc lập.
- Nếu dùng đơn lẻ, mô hình có thể giúp giảm drawdown nhưng dễ underperform trong thị trường tăng.
- MACD hiện đóng vai trò benchmark mạnh hơn về khả năng bắt trend và tạo điểm/lợi nhuận.
- Buy & Hold vẫn mạnh khi thị trường có xu hướng tăng dài, nhưng rủi ro drawdown lớn hơn đáng kể.
- Việc Ito có beta thấp `0.247` cho thấy nó giảm phụ thuộc thị trường, nhưng cũng làm mất upside khi thị trường đi lên.

### Hướng Phát Triển

1. **Kết hợp Ito Bayes-GARCH với MACD regime filter**

   Chỉ cho Ito long khi MACD xác nhận trend tăng. Khi đó MACD xử lý hướng xu thế, còn Ito-GARCH xử lý volatility và rủi ro.

2. **Đổi từ long/cash sang position sizing theo volatility**

   Thay vì tín hiệu 0/1, dùng tỷ trọng:

   `weight_t = target_vol / forecast_volatility_t`

   Cách này giữ exposure khi drift dương nhưng giảm tỷ trọng trong giai đoạn volatility cao.

3. **Dùng xác suất dự báo thay cho drift đơn điểm**

   Có thể vào lệnh khi:

   `P(r_{t+1} > 0) > threshold`

   Cách này tận dụng posterior distribution tốt hơn so với chỉ dùng mean forecast.

4. **Thêm momentum và technical features vào drift**

   Drift có thể được mở rộng bằng các biến như MACD histogram, RSI, moving-average slope, volume regime hoặc realized volatility regime. Khi đó Ito-GARCH không chỉ là mô hình volatility mà trở thành mô hình return-risk có điều kiện.

5. **Walk-forward refit**

   Refit GARCH định kỳ theo rolling window để mô hình thích nghi với regime mới. Điều này đặc biệt quan trọng với VN-Index vì cấu trúc volatility thay đổi mạnh qua các giai đoạn khủng hoảng và hồi phục.

6. **Tối ưu objective theo mục tiêu nghiên cứu**

   Nếu mục tiêu là lợi nhuận, tối ưu CAGR/total points. Nếu mục tiêu là phòng thủ, tối ưu Sharpe/Calmar/max drawdown. Hiện objective đang cân bằng Sharpe, Calmar và CAGR nên Ito được chọn theo hướng phòng thủ.

## Tối Ưu Tham Số

Quy trình tối ưu dùng split theo thời gian `60% train / 20% validation / 20% test`. Tham số được chọn trên validation bằng score:

`Sharpe + 0.30 * Calmar + 0.20 * CAGR`

Test cuối không được dùng để chọn tham số.

Kết quả tối ưu gần nhất của bạn:

| Model | Best params | Validation score |
|---|---|---:|
| Ito Bayes-GARCH | `drift_window=126`, `prior_strength=63`, `risk_buffer=0.08` | 1.015 |
| MACD | `fast=6`, `slow=26`, `signal=12` | 1.603 |

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
- `outputs_optimization/optimization_report.md`: báo cáo tối ưu tham số.
- `outputs_optimization/optimized_test_comparison_formatted.csv`: bảng so sánh baseline/tối ưu trên test cuối.
- `outputs_optimization/optimized_equity_curve_test.png`: equity curve của baseline/tối ưu và buy-and-hold.
- `outputs_optimization/ito_validation_grid.csv`: grid search Ito.
- `outputs_optimization/macd_validation_grid.csv`: grid search MACD.
