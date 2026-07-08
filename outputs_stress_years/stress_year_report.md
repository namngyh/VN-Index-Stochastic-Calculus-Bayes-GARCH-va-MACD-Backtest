# Báo Cáo Stress-Year Backtest

## Phương Pháp Chọn Năm

Các năm stress được chọn từ chuỗi VN-Index benchmark return bằng composite score:

- annualized volatility cao,
- downside volatility cao,
- max drawdown sâu,
- annual return yếu.

Mỗi năm được backtest độc lập với capital reset về `1.0` ở đầu năm. Các năm được chọn: `2008, 2022, 2020, 2018, 2006`.

## Xếp Hạng Năm Stress

| year | sessions | benchmark_return | annual_volatility | max_drawdown | worst_day | stress_score |
| ---- | -------- | ---------------- | ----------------- | ------------ | --------- | ------------ |
| 2008 | 245      | -65.96%          | 37.05%            | -68.85%      | -4.69%    | 7            |
| 2022 | 249      | -32.78%          | 24.83%            | -40.34%      | -4.95%    | 16           |
| 2020 | 252      | 14.87%           | 22.79%            | -33.51%      | -6.28%    | 24           |
| 2018 | 248      | -9.32%           | 22.28%            | -26.21%      | -5.10%    | 26           |
| 2006 | 249      | 144.48%          | 32.27%            | -36.81%      | -4.84%    | 29           |
| 2009 | 251      | 56.78%           | 34.58%            | -30.32%      | -4.55%    | 31           |
| 2011 | 248      | -27.46%          | 21.15%            | -33.45%      | -4.03%    | 32           |
| 2007 | 248      | 23.31%           | 27.29%            | -24.50%      | -4.37%    | 38           |
| 2026 | 120      | 4.53%            | 21.16%            | -16.38%      | -6.51%    | 38           |
| 2010 | 250      | -2.05%           | 21.01%            | -22.86%      | -3.95%    | 39           |

## Backtest 3 Chiến Lược Trong Các Năm Stress

| year | strategy        | total_points | total_return | annual_volatility | sharpe | max_drawdown | var_95_daily | cvar_95_daily | win_rate | exposure | trades |
| ---- | --------------- | ------------ | ------------ | ----------------- | ------ | ------------ | ------------ | ------------- | -------- | -------- | ------ |
| 2008 | Ito Bayes-GARCH | 0.00         | 0.00%        | 0.00%             |        | 0.00%        | 0.00%        | 0.00%         | 0.00%    | 0.00%    | 0      |
| 2008 | MACD(6,26,12)   | -126.26      | -11.96%      | 22.57%            | -0.467 | -28.59%      | -2.74%       | -3.64%        | 25.31%   | 48.98%   | 9      |
| 2008 | Buy & Hold      | -611.42      | -65.96%      | 37.05%            | -2.800 | -68.85%      | -4.22%       | -4.47%        | 44.08%   | 100.00%  | 1      |
| 2022 | Ito Bayes-GARCH | -123.00      | -7.92%       | 5.12%             | -1.605 | -7.92%       | -0.05%       | -0.72%        | 2.41%    | 7.63%    | 6      |
| 2022 | MACD(6,26,12)   | -99.06       | -9.16%       | 15.06%            | -0.570 | -21.27%      | -1.66%       | -2.74%        | 24.90%   | 50.60%   | 9      |
| 2022 | Buy & Hold      | -491.19      | -32.78%      | 24.83%            | -1.494 | -40.34%      | -3.22%       | -4.06%        | 49.40%   | 100.00%  | 1      |
| 2020 | Ito Bayes-GARCH | 169.93       | 18.53%       | 6.88%             | 2.505  | -4.23%       | -0.42%       | -1.00%        | 19.44%   | 28.17%   | 4      |
| 2020 | MACD(6,26,12)   | 321.09       | 46.13%       | 13.62%            | 2.855  | -9.17%       | -1.04%       | -2.02%        | 40.08%   | 61.11%   | 8      |
| 2020 | Buy & Hold      | 142.88       | 14.87%       | 22.79%            | 0.723  | -33.51%      | -2.83%       | -4.16%        | 61.90%   | 100.00%  | 1      |
| 2018 | Ito Bayes-GARCH | 36.79        | 3.88%        | 11.60%            | 0.392  | -10.64%      | -0.70%       | -2.14%        | 17.34%   | 25.81%   | 1      |
| 2018 | MACD(6,26,12)   | 178.33       | 18.71%       | 12.30%            | 1.479  | -8.52%       | -1.42%       | -2.08%        | 38.31%   | 59.27%   | 8      |
| 2018 | Buy & Hold      | -91.70       | -9.32%       | 22.28%            | -0.334 | -26.21%      | -2.57%       | -3.52%        | 56.05%   | 100.00%  | 1      |
| 2006 | Ito Bayes-GARCH | 85.95        | 28.43%       | 26.42%            | 1.090  | -33.96%      | -3.14%       | -4.05%        | 26.91%   | 49.80%   | 5      |
| 2006 | MACD(6,26,12)   | 415.80       | 112.56%      | 22.80%            | 3.465  | -13.69%      | -1.73%       | -3.07%        | 28.92%   | 48.19%   | 7      |
| 2006 | Buy & Hold      | 444.27       | 144.48%      | 32.27%            | 2.969  | -36.81%      | -3.50%       | -4.15%        | 57.03%   | 100.00%  | 1      |

## Đọc Nhanh Theo Từng Năm

- `2008`: return tốt nhất là `Ito Bayes-GARCH` (0.00%); drawdown thấp nhất là `Ito Bayes-GARCH` (0.00%); Sharpe tốt nhất là `MACD(6,26,12)` (-0.467).
- `2022`: return tốt nhất là `Ito Bayes-GARCH` (-7.92%); drawdown thấp nhất là `Ito Bayes-GARCH` (-7.92%); Sharpe tốt nhất là `MACD(6,26,12)` (-0.570).
- `2020`: return tốt nhất là `MACD(6,26,12)` (46.13%); drawdown thấp nhất là `Ito Bayes-GARCH` (-4.23%); Sharpe tốt nhất là `MACD(6,26,12)` (2.855).
- `2018`: return tốt nhất là `MACD(6,26,12)` (18.71%); drawdown thấp nhất là `MACD(6,26,12)` (-8.52%); Sharpe tốt nhất là `MACD(6,26,12)` (1.479).
- `2006`: return tốt nhất là `Buy & Hold` (144.48%); drawdown thấp nhất là `MACD(6,26,12)` (-13.69%); Sharpe tốt nhất là `MACD(6,26,12)` (3.465).

## Nhận Xét Tổng Quát

- Ito Bayes-GARCH là bộ lọc phòng thủ dựa trên volatility và drift. Mô hình giảm exposure rất mạnh trong năm giảm sâu, nhờ đó kiểm soát drawdown tốt, nhưng dễ bỏ lỡ pha hồi phục nhanh.
- MACD(6,26,12) phản ứng tốt hơn với trend và momentum. Vì vậy MACD thường vượt trội ở các năm có hồi phục rõ hoặc xu hướng tăng mạnh sau cú sốc.
- Buy & Hold thắng khi cả năm có xu hướng tăng rất mạnh, nhưng chịu toàn bộ drawdown và tail risk trong giai đoạn bán tháo.
- Kết quả stress-test gợi ý hướng phát triển hợp lý là dùng MACD để xác nhận xu hướng, còn Ito Bayes-GARCH làm lớp quản trị rủi ro, điều chỉnh exposure hoặc position sizing.
