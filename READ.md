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

   VN-Index chịu ảnh hưởng của dòng tiền, chính sách, tâm lý, thanh khoản và regime vĩ mô. Mô hình Ito-Bayes-GARCH hiện tại chủ yếu dùng chuỗi giá/return và volatility, nên chưa có thông tin trend, momentum, volume, macro hoặc regime filter. Vì vậy mô hình có nền tảng mô hình hóa tốt nhưng chưa đủ thông tin để cạnh tranh với một rule momentum đơn giản trong giai đoạn thị trường có xu hướng.

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

## Stress-Test Các Năm Khó Khăn Và Biến Động Mạnh Nhất

Mục tiêu của phần này là kiểm tra 3 chiến lược trong những năm mà VN-Index có điều kiện thị trường khó: volatility cao, downside volatility cao, drawdown sâu, hoặc annual return yếu. Mỗi năm được backtest độc lập với capital reset về `1.0` từ đầu năm để tránh việc kết quả của năm trước làm méo kết quả của năm sau.

Script dùng để chạy lại:

```bash
/home/namngyh/miniconda3/envs/eda/bin/python stress_year_backtest.py
```

Output được lưu tại:

- `outputs_stress_years/stress_year_ranking.csv`
- `outputs_stress_years/stress_year_metrics.csv`
- `outputs_stress_years/stress_year_metrics_formatted.csv`
- `outputs_stress_years/stress_year_report.md`
- `outputs_stress_years/stress_year_ranking.png`
- `outputs_stress_years/stress_year_equity_curves.png`
- `outputs_stress_years/stress_year_drawdowns.png`
- `outputs_stress_years/stress_year_metric_heatmap.png`

### Phương Pháp Chọn Năm Stress

Các năm stress được chọn bằng composite stress score từ dữ liệu Buy & Hold/VN-Index. Score này xếp hạng từng năm theo 4 nhóm rủi ro:

1. Annualized volatility cao.
2. Downside volatility cao.
3. Max drawdown sâu.
4. Annual return yếu.

Điểm stress càng thấp thì năm đó càng khó. 5 năm được chọn tự động là `2008`, `2022`, `2020`, `2018`, `2006`.

| Year | Sessions | VN-Index return | Annual volatility | Max drawdown | Worst day | Stress score |
|---|---:|---:|---:|---:|---:|---:|
| 2008 | 245 | -65.96% | 37.05% | -68.85% | -4.69% | 7 |
| 2022 | 249 | -32.78% | 24.83% | -40.34% | -4.95% | 16 |
| 2020 | 252 | 14.87% | 22.79% | -33.51% | -6.28% | 24 |
| 2018 | 248 | -9.32% | 22.28% | -26.21% | -5.10% | 26 |
| 2006 | 249 | 144.48% | 32.27% | -36.81% | -4.84% | 29 |
| 2009 | 251 | 56.78% | 34.58% | -30.32% | -4.55% | 31 |
| 2011 | 248 | -27.46% | 21.15% | -33.45% | -4.03% | 32 |
| 2007 | 248 | 23.31% | 27.29% | -24.50% | -4.37% | 38 |
| 2026 | 120 | 4.53% | 21.16% | -16.38% | -6.51% | 38 |
| 2010 | 250 | -2.05% | 21.01% | -22.86% | -3.95% | 39 |

Lưu ý quan trọng: `2006` không phải năm giảm, nhưng vẫn lọt nhóm stress vì volatility `32.27%`, downside volatility cao và max drawdown `-36.81%`. Đây là một năm tăng mạnh nhưng rung lắc cực lớn, nên phù hợp để kiểm tra liệu chiến lược có giữ được upside khi thị trường đi lên trong biến động cao hay không.

![Stress-year ranking](outputs_stress_years/stress_year_ranking.png)

### Bảng Backtest Theo Từng Năm Stress

| Year | Strategy | Total points | Total return | Annual volatility | Sharpe | Sortino | Max drawdown | VaR 95% daily | CVaR 95% daily | Win rate | Exposure | Trades |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2008 | Ito Bayes-GARCH | 0.00 | 0.00% | 0.00% |  |  | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0 |
| 2008 | MACD(6,26,12) | -126.26 | -11.96% | 22.57% | -0.467 | -0.509 | -28.59% | -2.74% | -3.64% | 25.31% | 48.98% | 9 |
| 2008 | Buy & Hold | -611.42 | -65.96% | 37.05% | -2.800 | -5.134 | -68.85% | -4.22% | -4.47% | 44.08% | 100.00% | 1 |
| 2022 | Ito Bayes-GARCH | -123.00 | -7.92% | 5.12% | -1.605 | -0.660 | -7.92% | -0.05% | -0.72% | 2.41% | 7.63% | 6 |
| 2022 | MACD(6,26,12) | -99.06 | -9.16% | 15.06% | -0.570 | -0.514 | -21.27% | -1.66% | -2.74% | 24.90% | 50.60% | 9 |
| 2022 | Buy & Hold | -491.19 | -32.78% | 24.83% | -1.494 | -1.914 | -40.34% | -3.22% | -4.06% | 49.40% | 100.00% | 1 |
| 2020 | Ito Bayes-GARCH | 169.93 | 18.53% | 6.88% | 2.505 | 1.715 | -4.23% | -0.42% | -1.00% | 19.44% | 28.17% | 4 |
| 2020 | MACD(6,26,12) | 321.09 | 46.13% | 13.62% | 2.855 | 2.801 | -9.17% | -1.04% | -2.02% | 40.08% | 61.11% | 8 |
| 2020 | Buy & Hold | 142.88 | 14.87% | 22.79% | 0.723 | 0.736 | -33.51% | -2.83% | -4.16% | 61.90% | 100.00% | 1 |
| 2018 | Ito Bayes-GARCH | 36.79 | 3.88% | 11.60% | 0.392 | 0.202 | -10.64% | -0.70% | -2.14% | 17.34% | 25.81% | 1 |
| 2018 | MACD(6,26,12) | 178.33 | 18.71% | 12.30% | 1.479 | 1.434 | -8.52% | -1.42% | -2.08% | 38.31% | 59.27% | 8 |
| 2018 | Buy & Hold | -91.70 | -9.32% | 22.28% | -0.334 | -0.428 | -26.21% | -2.57% | -3.52% | 56.05% | 100.00% | 1 |
| 2006 | Ito Bayes-GARCH | 85.95 | 28.43% | 26.42% | 1.090 | 1.242 | -33.96% | -3.14% | -4.05% | 26.91% | 49.80% | 5 |
| 2006 | MACD(6,26,12) | 415.80 | 112.56% | 22.80% | 3.465 | 3.996 | -13.69% | -1.73% | -3.07% | 28.92% | 48.19% | 7 |
| 2006 | Buy & Hold | 444.27 | 144.48% | 32.27% | 2.969 | 4.547 | -36.81% | -3.50% | -4.15% | 57.03% | 100.00% | 1 |

![Stress-year equity curves](outputs_stress_years/stress_year_equity_curves.png)

![Stress-year drawdowns](outputs_stress_years/stress_year_drawdowns.png)

![Stress-year metric heatmap](outputs_stress_years/stress_year_metric_heatmap.png)

### Nhận Xét Chi Tiết Theo Từng Năm

**Năm 2008: khủng hoảng giảm sâu, VN-Index mất `-65.96%`**

Đây là năm stress nặng nhất trong toàn bộ mẫu: annual volatility `37.05%`, max drawdown `-68.85%`, worst day `-4.69%`. Buy & Hold chịu toàn bộ cú sụp của thị trường, mất `-611.42` điểm và total return `-65.96%`. MACD giảm thiệt hại đáng kể so với Buy & Hold, nhưng vẫn lỗ `-11.96%` và max drawdown `-28.59%` vì chiến lược trend-following vẫn có các pha vào lệnh sai trong bear market.

Ito Bayes-GARCH đứng ngoài hoàn toàn: exposure `0.00%`, trades `0`, return `0.00%`, drawdown `0.00%`. Điều này cho thấy mô hình rất nhạy với trạng thái rủi ro cao và drift bất lợi. Trong bối cảnh khủng hoảng giảm một chiều, đây là ưu điểm lớn: mô hình bảo toàn vốn tốt nhất. Nhưng cũng cần hiểu rằng kết quả này không phải do mô hình dự báo tăng tốt, mà do mô hình từ chối tham gia thị trường khi điều kiện stochastic return-risk không đạt ngưỡng.

**Năm 2022: bear market hiện đại, thanh khoản và tâm lý xấu**

VN-Index giảm `-32.78%`, max drawdown `-40.34%`, annual volatility `24.83%`. Buy & Hold mất `-491.19` điểm và chịu tail risk rõ rệt với daily CVaR 95% `-4.06%`. MACD giảm lỗ xuống `-9.16%`, nhưng max drawdown vẫn `-21.27%` vì chiến lược có exposure `50.60%` trong một năm nhiều nhịp hồi giả.

Ito Bayes-GARCH là chiến lược ít lỗ nhất với total return `-7.92%` và drawdown `-7.92%`. Exposure chỉ `7.63%`, cho thấy mô hình gần như chuyển sang cash trong phần lớn năm. Tuy nhiên Sharpe `-1.605` vẫn xấu vì những lần vào lệnh hiếm hoi không tạo được lợi nhuận đủ lớn. Đây là bằng chứng quan trọng: Ito quản trị rủi ro tốt, nhưng khi tín hiệu entry quá ít và không đủ chính xác, hiệu quả return-adjusted vẫn có thể yếu.

**Năm 2020: cú sốc mạnh nhưng hồi phục nhanh**

Năm 2020 có worst day `-6.28%`, max drawdown Buy & Hold `-33.51%`, nhưng annual return cả năm vẫn dương `14.87%` nhờ pha hồi phục mạnh. Đây là môi trường rất khác 2008 và 2022: thị trường giảm sốc rồi chuyển sang trend tăng.

MACD thắng rõ rệt với total return `46.13%`, `321.09` điểm, Sharpe `2.855`. Lý do chính là MACD phản ứng tốt với momentum hồi phục, exposure `61.11%` giúp chiến lược tham gia nhiều hơn vào pha tăng. Ito Bayes-GARCH cũng tốt với return `18.53%` và drawdown chỉ `-4.23%`, nhưng exposure `28.17%` làm mô hình bỏ lỡ một phần lớn upside. Buy & Hold chỉ đạt `14.87%` vì chịu trọn cú rơi đầu năm.

Kết luận năm 2020: MACD tốt nhất khi thị trường có reversal và trend hồi phục rõ; Ito phù hợp nếu ưu tiên drawdown thấp hơn lợi nhuận tuyệt đối.

**Năm 2018: thị trường âm nhưng có nhịp xu hướng đủ rõ**

Buy & Hold giảm `-9.32%`, max drawdown `-26.21%`. Đây là năm không sụp như 2008 nhưng đủ khó vì xu hướng tổng thể yếu và biến động cao. MACD đạt total return `18.71%`, Sharpe `1.479`, max drawdown `-8.52%`, vượt cả Ito và Buy & Hold. Điểm đáng chú ý là MACD không chỉ thắng về return mà còn thắng luôn về drawdown trong năm này.

Ito đạt return `3.88%`, drawdown `-10.64%`, exposure `25.81%`. Mô hình có bảo vệ vốn nhưng chưa khai thác tốt các nhịp tăng trong năm. Với chỉ `1` entry, Ito có vẻ quá thận trọng trong bối cảnh thị trường không giảm một chiều. Khi thị trường dao động nhưng vẫn có những trend trung hạn, MACD có lợi thế hơn.

**Năm 2006: tăng rất mạnh nhưng rủi ro nội năm cao**

VN-Index tăng `144.48%`, nhưng annual volatility `32.27%` và max drawdown `-36.81%`. Đây là năm cho thấy khác biệt giữa stress do giảm giá và stress do biến động cao. Buy & Hold thắng về total return vì nắm giữ toàn bộ xu hướng tăng, đạt `444.27` điểm và `144.48%`.

MACD đứng thứ hai về return với `112.56%`, nhưng là chiến lược kiểm soát drawdown tốt nhất: `-13.69%` so với Buy & Hold `-36.81%` và Ito `-33.96%`. Điều này cho thấy MACD lọc bớt các pha giảm mạnh mà vẫn giữ được phần lớn xu hướng tăng. Ito chỉ đạt `28.43%`, thấp hơn nhiều vì exposure `49.80%` nhưng các entry không tối ưu bằng MACD; thêm nữa, risk buffer làm mô hình rời thị trường trong một số đoạn tăng biến động cao.

### So Sánh Tổng Quát Trong Nhóm Năm Stress

**Ito Bayes-GARCH**

- Mạnh nhất trong môi trường giảm sâu hoặc rủi ro hệ thống rõ: `2008` và `2022`.
- Drawdown thường thấp hơn Buy & Hold rất nhiều nhờ exposure thấp.
- Điểm yếu là bỏ lỡ upside khi thị trường hồi nhanh hoặc tăng mạnh: `2020`, `2018`, `2006`.
- Khi volatility cao nhưng trend tăng vẫn bền, mô hình có thể quá bảo thủ vì drift kỳ vọng không vượt đủ ngưỡng so với volatility.

**MACD(6,26,12)**

- Mạnh nhất trong các năm có trend hồi phục hoặc momentum đủ rõ: `2020`, `2018`, `2006`.
- Trong `2008`, MACD vẫn giảm nhưng mức lỗ nhỏ hơn Buy & Hold rất nhiều.
- MACD có ưu thế thực nghiệm vì nó trực tiếp bám vào cấu trúc xu hướng giá, trong khi Ito Bayes-GARCH chủ yếu nhìn return-risk và volatility.
- Điểm yếu là vẫn có thể bị whipsaw trong bear market, thể hiện qua drawdown `-28.59%` năm `2008` và `-21.27%` năm `2022`.

**Buy & Hold**

- Tốt nhất khi thị trường tăng cực mạnh và trend dài: `2006`.
- Rất yếu trong năm giảm sâu: `2008` và `2022`.
- Đây là benchmark quan trọng vì nó cho biết phần lợi nhuận đến từ beta thị trường thuần túy. Trong stress-test, Buy & Hold có upside lớn nhưng risk-adjusted không ổn định.

### Kết Luận Từ Stress-Test

Stress-test củng cố kết luận của backtest chính: Ito Bayes-GARCH không nên được xem là chiến lược alpha độc lập mạnh nhất, mà phù hợp hơn như một risk filter hoặc volatility-aware allocation layer. Mô hình này có giá trị lớn trong việc giảm thiệt hại ở năm xấu, nhưng đánh đổi bằng việc bỏ lỡ lợi nhuận trong năm hồi phục mạnh.

MACD(6,26,12) là benchmark giao dịch mạnh hơn trong dữ liệu hiện tại vì bắt được momentum và regime hồi phục tốt hơn. Tuy nhiên MACD không bảo vệ vốn tuyệt đối trong khủng hoảng giảm một chiều. Vì vậy hướng phát triển hợp lý nhất là kết hợp: dùng MACD để xác nhận trend, dùng Ito Bayes-GARCH để điều chỉnh exposure, position sizing hoặc giảm tỷ trọng khi volatility/tail risk tăng cao.

## Hybrid Defensive Exposure Framework

Phiên bản này phát triển tiếp mô hình theo đúng triết lý: **MACD = alpha engine**, còn **Ito-Bayes-GARCH Defensive Exposure Model = risk governor / capital allocation engine**. Ito-Bayes-GARCH không còn bị ép trở thành standalone alpha generator. Thay vào đó, nó quyết định nên cấp bao nhiêu vốn cho tín hiệu MACD trong điều kiện volatility, tail risk và Bayesian uncertainty hiện tại.

Script chạy lại:

```bash
/home/namngyh/miniconda3/envs/eda/bin/python run_hybrid_experiment.py
```

Config chính nằm tại `config.yaml`. Output nằm tại `outputs_hybrid_defensive_exposure/`.

### Kiến Trúc

Công thức lõi:

`position_t = MACD_signal_t × risk_allocation_t`

Các biến thể đã backtest:

- Buy & Hold.
- MACD only.
- Ito-Bayes-GARCH only.
- MACD + Ito hard gate.
- MACD + volatility targeting.
- MACD + tail-risk gate.
- MACD + full defensive exposure model.

Full defensive exposure model dùng:

- Volatility targeting: giảm position khi forecast volatility cao.
- Tail-risk hard exit: thoát nếu `forecast_return_p05 < loss_floor`.
- Bayesian uncertainty penalty: proxy bằng độ rộng predictive interval chuẩn hóa `(forecast_p95 - forecast_p05) / (3.29 × forecast_volatility) - 1`.
- Profit protection: nếu trade đang có lãi nhưng volatility xấu đi, cap exposure.
- Equity protection: nếu equity drawdown vượt warning/danger threshold, giảm hoặc tắt exposure.
- Regime detection: report-only diagnostic, chưa trực tiếp điều khiển position.

### Phương Pháp Backtest

- VN-Index only.
- Long/cash only, không short.
- Transaction cost `0.05%` mỗi lần thay đổi position.
- Ito-Bayes-GARCH forecast dùng walk-forward yearly: mỗi năm chỉ fit bằng dữ liệu trước năm đó.
- MACD signal được shift 1 phiên.
- Position có thể là fractional exposure trong `[0, 1]`.

### Bảng So Sánh Hybrid

| Strategy | Total return | CAGR | Annual vol | Sharpe | Sortino | Calmar | Max drawdown | CVaR 95% daily | Exposure | Trades |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Buy & Hold | 506.32% | 9.31% | 22.33% | 0.511 | 0.670 | 0.116 | -79.88% | -3.51% | 100.00% | 1 |
| MACD only | 5956.38% | 22.46% | 14.28% | 1.490 | 1.562 | 0.678 | -33.13% | -2.19% | 54.11% | 192 |
| Ito-Bayes-GARCH only | 259.32% | 6.52% | 12.08% | 0.583 | 0.442 | 0.173 | -37.58% | -2.05% | 32.37% | 133 |
| MACD + Ito hard gate | 452.55% | 8.81% | 8.34% | 1.053 | 0.661 | 0.508 | -17.33% | -1.18% | 19.20% | 127 |
| MACD + volatility targeting | 936.60% | 12.24% | 8.78% | 1.359 | 1.387 | 0.625 | -19.57% | -1.37% | 40.29% | 192 |
| MACD + tail-risk gate | 352.52% | 7.74% | 9.03% | 0.871 | 0.741 | 0.397 | -19.49% | -1.49% | 38.28% | 241 |
| MACD + full defensive exposure | 197.97% | 5.54% | 6.86% | 0.821 | 0.690 | 0.376 | -14.72% | -1.13% | 29.78% | 241 |

### Trả Lời Các Câu Hỏi Chính

- Hybrid model có giảm max drawdown so với MACD only không? Có. Full defensive giảm từ `-33.13%` xuống `-14.72%`.
- Hybrid model có giữ max drawdown trên ngưỡng `-15%` không? Có, đạt `-14.72%`.
- Hybrid model có cải thiện Calmar so với MACD only không? Không. MACD only `0.678`, full defensive `0.376`.
- Hybrid model có cải thiện Sortino so với MACD only không? Không. MACD only `1.562`, full defensive `0.690`.
- Hybrid hy sinh bao nhiêu raw return? Full defensive đạt `197.97%` so với MACD only `5956.38%`, tức hy sinh rất lớn để đổi lấy drawdown control.
- Model outperform trong regime nào? Full defensive hữu ích nhất ở panic/stress vì exposure giảm rất mạnh, ví dụ năm `2022` chỉ drawdown `-2.83%` và năm `2008` drawdown `-6.15%`.
- Model underperform trong regime nào? Trend_up và recovery, vì risk governor quá bảo thủ và không cấp đủ vốn cho MACD khi xu hướng tăng mạnh.
- Ito-Bayes-GARCH layer có tạo giá trị như risk governor không? Có nếu mục tiêu là tail-risk và max drawdown constraint; chưa đủ tốt nếu mục tiêu là Calmar/Sortino vượt MACD.
- Nên dùng hard gate, soft sizing hay hybrid? Với kết quả hiện tại, soft sizing bằng volatility targeting là cân bằng hơn về return/risk; full defensive phù hợp khi constraint drawdown `-15%` là bắt buộc.

### Biểu Đồ Hybrid

![Hybrid equity curves](outputs_hybrid_defensive_exposure/equity_curves.png)

![Hybrid drawdown curves](outputs_hybrid_defensive_exposure/drawdown_curves.png)

![Hybrid position exposure](outputs_hybrid_defensive_exposure/position_exposure.png)

![Hybrid risk allocation components](outputs_hybrid_defensive_exposure/risk_allocation_components.png)

![Hybrid regime chart](outputs_hybrid_defensive_exposure/regime_chart.png)

### Kết Luận Hybrid

Full defensive exposure model đáng dùng hơn MACD only nếu mục tiêu bắt buộc là giữ drawdown quanh `-15%` và giảm tail-risk. Nếu mục tiêu là raw return, Calmar hoặc Sortino, MACD only vẫn tốt hơn trong cấu hình hiện tại. Tham số nhạy cảm nhất là `target_volatility`, `loss_floor`, `uncertainty_penalty_k` và ngưỡng `danger_drawdown`. Bước tiếp theo nên tối ưu các tham số risk governor trên validation, không tối ưu trên test.

## Tối Ưu Tham Số Hybrid Risk Governor

Sau khi xây dựng hybrid framework, bước tiếp theo là tối ưu riêng lớp risk governor thay vì tối ưu MACD alpha. Script:

```bash
/home/namngyh/miniconda3/envs/eda/bin/python optimize_hybrid_risk_governor.py
```

Quy trình:

- MACD(6,26,12) được giữ cố định là alpha engine.
- Forecast Ito-Bayes-GARCH vẫn walk-forward yearly.
- Grid-search chỉ chạy trên validation.
- Test cuối không dùng để chọn tham số.
- Objective: `0.40*CAGR + 0.30*Calmar + 0.20*Sortino - turnover_penalty - drawdown_constraint_penalty - exposure_penalty`.
- Constraint chính: `max_drawdown >= -15%`.

### Best Params

| Parameter | Value | Ý nghĩa |
|---|---:|---|
| target_volatility | 25.00% | Nới volatility target để giữ nhiều upside hơn. |
| loss_floor | -2.50% | Tail-risk gate bớt quá chặt so với `-2.00%`. |
| uncertainty_penalty_k | 0.00 | Validation cho thấy uncertainty penalty hiện làm mất upside, nên tạm tắt. |
| profit_lock_threshold | 12.00% | Chỉ khóa lợi nhuận khi trade đã lời đủ lớn. |
| warning_drawdown | 10.00% | Nới ngưỡng cảnh báo drawdown. |
| danger_drawdown | 15.00% | Giữ sát constraint chính. |

### Final Test Sau Tối Ưu

| Strategy | Total return | CAGR | Annual vol | Sharpe | Sortino | Calmar | Max drawdown | CVaR 95% daily | Exposure | Trades |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Buy & Hold | 45.04% | 9.61% | 19.25% | 0.574 | 0.678 | 0.317 | -30.28% | -3.20% | 100.00% | 1 |
| MACD only | 66.48% | 13.41% | 11.97% | 1.111 | 1.000 | 0.630 | -21.27% | -2.01% | 54.95% | 40 |
| MACD + volatility targeting | 64.79% | 13.12% | 11.52% | 1.128 | 1.014 | 0.647 | -20.28% | -1.94% | 53.77% | 40 |
| MACD + tail-risk gate | 50.86% | 10.68% | 10.44% | 1.025 | 0.846 | 0.637 | -16.76% | -1.77% | 47.99% | 41 |
| MACD + full defensive exposure optimized | 43.34% | 9.29% | 8.94% | 1.039 | 0.857 | 0.626 | -14.84% | -1.46% | 39.57% | 41 |

### Nhận Xét Sau Tối Ưu

- Full defensive optimized đạt constraint `-15%`: max drawdown `-14.84%`.
- So với bản full defensive trước đó trên test, return cải thiện lên `43.34%` và exposure tăng lên `39.57%`.
- So với MACD only, drawdown giảm từ `-21.27%` xuống `-14.84%`, nhưng total return giảm từ `66.48%` xuống `43.34%`.
- Calmar của full defensive optimized `0.626`, gần MACD only `0.630`, nhưng vẫn thấp hơn volatility targeting `0.647`.
- Sortino của full defensive optimized `0.857`, thấp hơn MACD only `1.000` và volatility targeting `1.014`.
- Best params cho thấy risk governor mặc định quá bảo thủ: validation chọn `target_volatility=25%`, `uncertainty_penalty_k=0`, `warning_drawdown=10%`.

### Kết Luận Sau Tối Ưu

Bản optimized full defensive đáng dùng nếu ràng buộc drawdown `-15%` là bắt buộc. Nếu mục tiêu là cân bằng return/risk mà không bắt buộc `-15%`, `MACD + volatility targeting` hiện là ứng viên tốt hơn vì có Calmar và Sortino cao hơn trong test. Điều này gợi ý hướng phát triển tiếp theo: giữ volatility targeting làm lõi sizing, sau đó thêm tail-risk/profit protection nhẹ hơn thay vì hard defensive quá mạnh.

![Optimized validation scores](outputs_hybrid_optimization/hybrid_validation_top_scores.png)

![Optimized test equity](outputs_hybrid_optimization/optimized_test_equity_curves.png)

![Optimized test drawdown](outputs_hybrid_optimization/optimized_test_drawdown_curves.png)

![Optimized test exposure](outputs_hybrid_optimization/optimized_test_position_exposure.png)

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
- `stress_year_backtest.py`: script stress-test 3 chiến lược trong các năm biến động mạnh nhất.
- `outputs_stress_years/stress_year_report.md`: báo cáo stress-test tự động.
- `outputs_stress_years/stress_year_metrics.csv`: bảng stress-test raw numeric.
- `outputs_stress_years/stress_year_metrics_formatted.csv`: bảng stress-test đã format.
- `outputs_stress_years/stress_year_ranking.csv`: bảng xếp hạng năm stress.
- `outputs_stress_years/stress_year_ranking.png`: biểu đồ ranking năm stress.
- `outputs_stress_years/stress_year_equity_curves.png`: equity curve theo từng năm stress.
- `outputs_stress_years/stress_year_drawdowns.png`: drawdown theo từng năm stress.
- `outputs_stress_years/stress_year_metric_heatmap.png`: heatmap so sánh chỉ số stress-test.
- `run_hybrid_experiment.py`: script chạy hybrid defensive exposure framework.
- `optimize_hybrid_risk_governor.py`: script tối ưu tham số hybrid risk governor trên validation.
- `config.yaml`: config tham số hybrid.
- `src/`: các module hybrid framework.
- `outputs_hybrid_defensive_exposure/hybrid_model_report.md`: báo cáo hybrid đầy đủ.
- `outputs_hybrid_defensive_exposure/strategy_comparison.csv`: bảng so sánh chiến lược hybrid.
- `outputs_hybrid_defensive_exposure/year_by_year_performance.csv`: hiệu suất từng năm.
- `outputs_hybrid_defensive_exposure/stress_period_performance.csv`: hiệu suất các năm stress.
- `outputs_hybrid_defensive_exposure/trade_statistics.csv`: thống kê lệnh.
- `outputs_hybrid_defensive_exposure/regime_performance.csv`: hiệu suất theo regime diagnostic.
- `outputs_hybrid_defensive_exposure/equity_curves.png`: equity curves hybrid.
- `outputs_hybrid_defensive_exposure/drawdown_curves.png`: drawdown curves hybrid.
- `outputs_hybrid_defensive_exposure/position_exposure.png`: chart position/exposure.
- `outputs_hybrid_defensive_exposure/risk_allocation_components.png`: chart thành phần risk allocation.
- `outputs_hybrid_defensive_exposure/regime_chart.png`: chart regime diagnostic.
- `outputs_hybrid_optimization/hybrid_optimization_report.md`: báo cáo tối ưu hybrid risk governor.
- `outputs_hybrid_optimization/hybrid_validation_grid.csv`: toàn bộ grid-search validation.
- `outputs_hybrid_optimization/test_strategy_comparison.csv`: bảng test cuối sau tối ưu.
- `outputs_hybrid_optimization/optimized_config.yaml`: config chứa best params.
- `outputs_hybrid_optimization/hybrid_validation_top_scores.png`: top validation scores.
- `outputs_hybrid_optimization/optimized_test_equity_curves.png`: equity test sau tối ưu.
- `outputs_hybrid_optimization/optimized_test_drawdown_curves.png`: drawdown test sau tối ưu.
- `outputs_hybrid_optimization/optimized_test_position_exposure.png`: position/exposure test sau tối ưu.
