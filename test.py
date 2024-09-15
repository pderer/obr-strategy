import datetime as dt

import numpy as np
import yfinance as yf  # type: ignore

stock_list = ["GEHC"]


def get_stock(ticker):
    stock = yf.Ticker(ticker)
    start_date = dt.datetime.strptime("2024-09-13", "%Y-%m-%d").date()
    data = stock.history(start=start_date - dt.timedelta(days=30), interval="5m")
    # recent_data = data[
    #     data.index.tz_localize(None)
    #     >= dt.datetime.combine(start_date, dt.datetime.min.time())
    #     - dt.timedelta(days=14)
    # ]
    # print(data)
    first_data = stock.history(start=start_date, interval="5m")

    if len(first_data) == 0:
        return None

    # 첫 5분 거래량
    first_5min_volume = first_data["Volume"].iloc[0]
    volumes = []
    for day, group in reversed(list(data.groupby(data.index.date))):
        print(group)
        first_5min = group.iloc[0]  # 첫 5분의 데이터
        volumes.append(first_5min["Volume"])
        if len(volumes) == 14:
            break
    print((first_5min_volume) / np.mean(volumes))


for stock in stock_list:
    get_stock(stock)
