# VN-Index Stochastic Calculus + Bayes-GARCH Strategy

Pipeline này kiểm định một chiến lược vào/ra lệnh cho VN-Index dựa trên:

- Chuyển động Brown hình học: `dS/S = mu dt + sigma dW`.
- Bổ đề Ito: `d log(S) = (mu - 0.5 sigma^2)dt + sigma dW`.
- Bayes-GARCH xấp xỉ: fit Student-t GARCH(1,1), sau đó lấy posterior xấp xỉ quanh nghiệm MLE để tạo dải bất định volatility.
- Bayesian rolling drift: ước lượng drift ngắn hạn và shrink về prior của tập train.

## Chạy lại

```bash
/home/namngyh/miniconda3/envs/eda/bin/python stochastic_ito_bayes_garch_strategy.py
```

Có thể thay đổi tham số:

```bash
/home/namngyh/miniconda3/envs/eda/bin/python stochastic_ito_bayes_garch_strategy.py \
  --start-date 2006-01-01 \
  --train-ratio 0.70 \
  --transaction-cost 0.0005 \
  --risk-buffer 0.08 \
  --drift-window 126 \
  --drift-prior-strength 63 \
  --macd-fast 6 \
  --macd-slow 26 \
  --macd-signal 12
```

## Output

Tất cả nằm trong `outputs_stochastic_calculus/`:

- `VN_Index_Stochastic_MACD_Backtest.ipynb`: notebook trực quan hóa và nhận xét chi tiết.
- `report.md`: báo cáo mô hình, split, forecast metrics và backtest metrics.
- `advanced_backtest_metrics.md`: bảng backtest chuyên sâu so sánh Full Data và Test.
- `advanced_backtest_metrics.csv`: dữ liệu chỉ số dạng raw để phân tích tiếp.
- `advanced_backtest_metrics_formatted.csv`: bảng chỉ số đã format để đọc nhanh.
- `full_data_backtest.csv`: signal, return và equity curve trên toàn bộ dữ liệu sau ngày bắt đầu.
- `forecast_train_test.png`: biểu đồ giá thực, train fit, test forecast và dải dự báo Brownian 90%.
- `backtest_equity_curve.png`: equity curve chiến lược so với buy-and-hold.
- `macd_indicator_test.png`: biểu đồ MACD line, signal line và histogram trên test.
- `macd_signals_on_price.png`: điểm long/exit của MACD trên giá.
- `drawdown_comparison_test.png`: so sánh drawdown Ito, MACD và buy-and-hold.
- `rolling_volatility_comparison_test.png`: rolling volatility 63 phiên.
- `return_distribution_test.png`: phân phối daily return.
- `signals_on_price.png`: điểm vào và thoát lệnh trên giá VN-Index.
- `forecast_volatility.png`: volatility năm hóa từ Bayes-GARCH.
- `predictions.csv`: dự báo train/test.
- `strategy_backtest.csv`: signal, return và equity curve trên test.
- `bayes_garch_posterior_draws.csv`: mẫu posterior xấp xỉ của tham số GARCH.

## Kết quả mặc định

- Train: 2006-01-03 đến 2020-05-13.
- Test: 2020-05-14 đến 2026-07-01.
- Directional accuracy test: khoảng 55%.
- Ito Bayes-GARCH có drawdown thấp hơn buy-and-hold trong test.
- MACD(6,26,12) sau tối ưu vượt buy-and-hold về total return và Sharpe trong test.

Đây là research backtest, chưa phải hệ thống giao dịch thực chiến. Bước tiếp theo nên là walk-forward refit, kiểm định nhạy phí giao dịch, threshold, và thêm bộ lọc regime.
