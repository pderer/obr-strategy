import concurrent.futures
import datetime as dt
from functools import partial

import numpy as np
import yfinance as yf  # type: ignore

OPEN_PRICE_THRESHOLD = 5.0
AVERAGE_VOLUME_THRESHOLD = 1_000_000
ATR_THRESHOLD = 0.5
LOOKBACK_DAYS = 14


def calculate_atr(data, period=14):
    high_low = data["High"] - data["Low"]
    high_close = np.abs(data["High"] - data["Close"].shift())
    low_close = np.abs(data["Low"] - data["Close"].shift())

    tr = np.maximum(high_low, np.maximum(high_close, low_close))
    atr = tr.rolling(period).mean()
    return atr


def process_ticker(ticker, start_date_time, end_date_time):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(
            start=start_date_time - dt.timedelta(days=30),
            end=end_date_time,
            interval="1d",
        )

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


# 병렬 처리로 모든 티커에 대해 필터링 적용
def filter_stocks_concurrently(stock_list, start_date_time, end_date_time):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        process_with_date = partial(
            process_ticker, start_date_time=start_date_time, end_date_time=end_date_time
        )
        results = list(executor.map(process_with_date, stock_list))
    filtered_stocks = [r for r in results if r is not None]
    return filtered_stocks
