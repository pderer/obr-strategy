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
today = dt.datetime.now(eastern)
fourteen_days_ago = today - dt.timedelta(days=14)

# 주식 목록 (필요시 Nasdaq 주식 목록을 사용)
filtered_df = pd.read_csv("filtered_stocks_by_ray.csv")
stock_list = filtered_df["Ticker"].tolist()  # 필터링된 주식 리스트를 여기에 입력
# stock_list = [
#     "AAPL",
#     "MSFT",
#     "GOOG",
#     "AMZN",
#     "TSLA",
# ]  # 테스트용, 나중에 전체 목록으로 변경 가능


# 최근 14일간 평균 첫 5분 거래량 계산 함수 (1개월 데이터를 가져와 계산)
@ray.remote
def get_average_first_5min_volume(ticker):
    stock = yf.Ticker(ticker)

    # 1개월 데이터 (5분 간격)
    data = stock.history(period="1mo", interval="5m")

    if len(data) == 0:
        return None

    # 최근 14일간의 데이터 필터링
    recent_data = data[data.index >= fourteen_days_ago]

    # 각 날짜의 첫 5분 거래량 계산
    volumes = []
    for day, group in recent_data.groupby(recent_data.index.date):
        first_5min = group.iloc[0]  # 첫 5분의 데이터
        volumes.append(first_5min["Volume"])

    # 평균 계산 (데이터가 있는 경우에만)
    if len(volumes) > 0:
        return np.mean(volumes)
    else:
        return None


# 첫 5분 거래량 계산 함수
@ray.remote
def get_first_5min_volume(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d", interval="5m")

    if len(data) == 0:
        return None

    # 첫 5분 거래량
    first_5min_volume = data["Volume"].iloc[0]
    return first_5min_volume


# 주식 데이터를 병렬로 처리하고 비율 계산
@ray.remote
def calculate_volume_ratio(ticker):
    try:
        # 오늘 첫 5분 거래량
        today_first_5min_volume = ray.get(get_first_5min_volume.remote(ticker))

        if today_first_5min_volume is None:
            return None

        # 최근 14일간의 첫 5분 평균 거래량
        avg_first_5min_volume = ray.get(get_average_first_5min_volume.remote(ticker))

        if avg_first_5min_volume is None:
            return None

        # 비율 계산 (오늘 첫 5분 거래량 / 최근 14일 평균 첫 5분 거래량)
        volume_ratio = (
            today_first_5min_volume / avg_first_5min_volume
            if avg_first_5min_volume != 0
            else 0
        )
        return (ticker, volume_ratio)

    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None


# 병렬로 주식 데이터를 처리
def process_stocks_concurrently(stock_list):
    futures = [calculate_volume_ratio.remote(stock) for stock in stock_list]
    results = ray.get(futures)
    stock_volumes = [result for result in results if result is not None]
    return stock_volumes


# 주식 데이터를 병렬로 처리한 후 내림차순 정렬
stock_volumes = process_stocks_concurrently(stock_list)

# 비율에 따른 내림차순 정렬
sorted_stocks = sorted(stock_volumes, key=lambda x: x[1], reverse=True)

top_30_stocks = sorted_stocks[:30]

# 정렬된 결과 출력
sorted_df = pd.DataFrame(top_30_stocks, columns=["Ticker", "Volume Ratio"])
print(sorted_df)
sorted_df.to_csv("volume_ratio_score.csv", index=False)

# Ray 종료
ray.shutdown()
