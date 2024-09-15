import concurrent.futures
import datetime as dt

import numpy as np
import pandas as pd
import yfinance as yf  # type: ignore

start_date = dt.datetime.strptime("2024-09-13", "%Y-%m-%d").date()


def get_average_first_5min_volume(ticker):
    stock = yf.Ticker(ticker)
    # 1개월 데이터 (5분 간격)
    # TODO: 백테스트 기간 설정하고 싶으면 end 수정해야 함
    data = stock.history(start=(start_date - dt.timedelta(days=30)), interval="5m")

    if len(data) == 0:
        return None

    # 각 날짜의 첫 5분 거래량 계산
    volumes = []
    for day, group in reversed(list(data.groupby(data.index.date))):
        first_5min = group.iloc[0]  # 첫 5분의 데이터
        volumes.append(first_5min["Volume"])
        if len(volumes) == 14:
            break

    # 평균 계산 (데이터가 있는 경우에만)
    if len(volumes) > 0:
        return (ticker, (volumes[0] / np.mean(volumes)))
    else:
        return None


def filter_stocks_concurrently(date_range_dir):
    filtered_df = pd.read_csv(f"{date_range_dir}/filtered_stocks_by_ray.csv")
    stock_list = filtered_df["Ticker"].tolist()  # 필터링된 주식 리스트를 여기에 입력
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(get_average_first_5min_volume, stock_list))
    filtered_stocks = [r for r in results if r is not None]
    return filtered_stocks
