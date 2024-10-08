import concurrent.futures
from functools import partial

import numpy as np
import yfinance as yf  # type: ignore


def relative_volume_score(ticker, start_date_time, end_date_time):
    stock = yf.Ticker(ticker)
    data = stock.history(
        start=start_date_time,
        end=end_date_time,
        interval="5m",
    )

    if len(data) == 0:
        return None

    end_date = end_date_time.date()
    end_date_volume = 0
    volumes = []

    # 장 시작 후 첫 5분 거래량 / 최근 14일의 첫 5분 거래량의 값
    for day, group in reversed(list(data.groupby(data.index.date))):
        first_5min = group.iloc[0]  # 첫 5분의 데이터
        if day == end_date:
            end_date_volume = first_5min["Volume"]
        else:
            volumes.append(first_5min["Volume"])
        if len(volumes) == 14:
            break

    if len(volumes) > 0:
        return (ticker, (end_date_volume / np.mean(volumes)))
    else:
        return None


def filter_stocks_concurrently(stock_list, start_date_time, end_date_time):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        process_with_date = partial(
            relative_volume_score,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )
        results = list(executor.map(process_with_date, stock_list))
    filtered_stocks = [r for r in results if r is not None]
    return filtered_stocks
