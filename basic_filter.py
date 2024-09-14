import datetime as dt

import numpy as np
import pandas as pd
import pytz
import ray
import yfinance as yf  # type: ignore

# Ray 초기화
ray.init()

# 미국 동부 시간대 설정 (EST/EDT)
eastern = pytz.timezone("US/Eastern")
today_eastern = dt.datetime.now(eastern).strftime("%Y-%m-%d")

# 필터링 조건
OPEN_PRICE_THRESHOLD = 5.0
AVERAGE_VOLUME_THRESHOLD = 1_000_000
ATR_THRESHOLD = 0.5
LOOKBACK_DAYS = 14

# 주식 목록 (필요시 Nasdaq 주식 목록을 사용)
stock_df = pd.read_csv(
    "/Users/pderer/trading/dev/US-Stock-Symbols/all/all_tickers.txt",
    header=None,
    names=["Symbol"],
)
stock_list = stock_df["Symbol"].unique().tolist()
if stock_list.len() == 0:
    exit
# stock_list = [
#     "AAPL",
#     "MSFT",
#     "GOOG",
#     "AMZN",
#     "TSLA",
# ]  # 테스트용, 나중에 전체 목록으로 변경 가능


# ATR 계산 함수
def calculate_atr(data, period=14):
    high_low = data["High"] - data["Low"]
    high_close = np.abs(data["High"] - data["Close"].shift())
    low_close = np.abs(data["Low"] - data["Close"].shift())

    tr = np.maximum(high_low, np.maximum(high_close, low_close))
    atr = tr.rolling(period).mean()
    return atr


# 주식 데이터 필터링 함수 (Ray를 이용한 비동기 처리)
@ray.remote
def filter_stock(ticker):
    try:
        stock = yf.Ticker(ticker)

        # 최근 14일간의 주식 데이터를 가져오기
        data = stock.history(period="1mo", interval="1d")
        recent_data = data.tail(14)

        if len(recent_data) < LOOKBACK_DAYS:
            return None  # 충분한 데이터가 없는 경우

        # 조건 1: 시가가 5불 이상인가?
        if recent_data["Open"].iloc[-1] < OPEN_PRICE_THRESHOLD:
            return None

        # 조건 2: 최근 14일간 평균 거래량이 100만 주 이상인가?
        avg_volume = recent_data["Volume"].mean()
        if avg_volume < AVERAGE_VOLUME_THRESHOLD:
            return None

        # 조건 3: 최근 14일 ATR(0.5불 이상)인가?
        atr = calculate_atr(recent_data, period=LOOKBACK_DAYS)
        if atr.iloc[-1] < ATR_THRESHOLD:
            return None

        # 모든 조건을 만족하면 티커를 반환
        return ticker

    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None


# 병렬로 주식 필터링
def process_stocks_concurrently(stock_list):
    futures = [filter_stock.remote(stock) for stock in stock_list]
    results = ray.get(futures)
    filtered_stocks = [result for result in results if result is not None]
    return filtered_stocks


# 필터링된 주식 목록 가져오기
filtered_stocks = process_stocks_concurrently(stock_list)

# 결과 출력
print(f"Filtered stocks: {filtered_stocks}")
filtered_df = pd.DataFrame(filtered_stocks, columns=["Ticker"])
filtered_df.to_csv("filtered_stocks_by_ray.csv", index=False)

# Ray 종료
ray.shutdown()
