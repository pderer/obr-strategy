import numpy as np
import pandas as pd
import pytz
import ray
import yfinance as yf  # type: ignore

# Ray 초기화
ray.init()

# 미국 동부 시간대 설정 (EST/EDT)
eastern = pytz.timezone("US/Eastern")

# 주식 목록 (필터링 후 상위 20개 주식, 예시로 사용)
filtered_df = pd.read_csv("volume_ratio_score.csv")
stock_list = filtered_df["Ticker"].tolist()  # 필터링된 주식 리스트를 여기에 입력
# stock_list = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA"]  # 상위 20개 주식으로 교체 필요


# ATR 계산 함수 (14일간)
def calculate_atr(data, period=14):
    high_low = data["High"] - data["Low"]
    high_close = np.abs(data["High"] - data["Close"].shift())
    low_close = np.abs(data["Low"] - data["Close"].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr


# 수익률 계산 함수
@ray.remote
def calculate_return_with_strategy(ticker):  # noqa: C901
    stock = yf.Ticker(ticker)

    # 5분 데이터
    data_5min = stock.history(period="1d", interval="5m")
    if len(data_5min) == 0:
        return None

    # 첫 5분 봉 데이터
    first_5min_open = data_5min["Open"].iloc[0]
    first_5min_close = data_5min["Close"].iloc[0]
    first_5min_high = data_5min["High"].iloc[0]
    first_5min_low = data_5min["Low"].iloc[0]

    # 당일 종가
    daily_close = data_5min["Close"].iloc[-1]

    # 14일간의 일일 데이터 (ATR 계산을 위한 데이터)
    data_daily = stock.history(period="1mo", interval="1d")
    if len(data_daily) < 14:
        return None

    # ATR 계산 (True Range)
    atr = calculate_atr(data_daily).iloc[-1]  # 가장 최신 ATR 값

    # ATR 기준 손절매 폭 설정 (ATR * 10%)
    stop_loss_threshold = atr * 0.10

    # 전략 적용 (양봉일 경우 고가 돌파 -> 롱 포지션)
    if first_5min_close > first_5min_open:  # 양봉
        for i in range(1, len(data_5min)):
            # 고가 돌파 시점 확인
            if data_5min["High"].iloc[i] > first_5min_high:
                # 롱 포지션 진입
                entry_price = first_5min_high

                # 손절매 체크
                for j in range(i + 1, len(data_5min)):
                    # 손절 조건: 현재 가격이 진입가보다 (ATR * 10%) 이하로 떨어지면 손절
                    if data_5min["Low"].iloc[j] < (entry_price - stop_loss_threshold):
                        return (ticker, (-stop_loss_threshold) / entry_price)

                # 손절이 발생하지 않으면 종가에 포지션 청산
                return (ticker, (daily_close - entry_price) / entry_price)

    # 전략 적용 (음봉일 경우 저가 하향 돌파 -> 숏 포지션)
    elif first_5min_close < first_5min_open:  # 음봉
        for i in range(1, len(data_5min)):
            # 저가 하향 돌파 시점 확인
            if data_5min["Low"].iloc[i] < first_5min_low:
                # 숏 포지션 진입
                entry_price = first_5min_low

                # 손절매 체크
                for j in range(i + 1, len(data_5min)):
                    # 손절 조건: 현재 가격이 진입가보다 (ATR * 10%) 이상 오르면 손절
                    if data_5min["High"].iloc[j] > (entry_price + stop_loss_threshold):
                        return (ticker, (-stop_loss_threshold) / entry_price)

                # 손절이 발생하지 않으면 종가에 포지션 청산
                return (ticker, (entry_price - daily_close) / entry_price)

    return None


# 주식 데이터를 병렬로 처리하고 수익률 계산
def process_stocks_for_return(stock_list):
    futures = [calculate_return_with_strategy.remote(stock) for stock in stock_list]
    results = ray.get(futures)
    stock_returns = [result for result in results if result is not None]
    return stock_returns


# 주식 데이터를 병렬로 처리하여 수익률 계산
stock_returns = process_stocks_for_return(stock_list)

# 결과 출력
returns_df = pd.DataFrame(stock_returns, columns=["Ticker", "Daily Return"])
head_20_returns_df = returns_df.head(20)
print(head_20_returns_df)

# 승률 계산
print(f"Hit Ratio: {((head_20_returns_df['Daily Return'] > 0).mean()):.2%}")

# 수익률 계산
average_return = head_20_returns_df["Daily Return"].sum()
print(f"Daily Total Return: {average_return:.2%}")

# Ray 종료
ray.shutdown()
