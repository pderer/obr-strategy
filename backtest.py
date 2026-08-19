import argparse
import os
from datetime import datetime, time

import pandas as pd
import pytz
from pandas.tseries.holiday import USFederalHolidayCalendar

from filters import (  # type: ignore  # noqa: F401
    basic_filter,
    relative_volume_score,
)
from returncalc import daily_return  # noqa: F401

# Copy-on-Write will become the new default in pandas 3.0
# 그 전까지 사용
pd.options.mode.copy_on_write = True

eastern = pytz.timezone("America/New_York")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
stock_symbols_path = os.path.join(
    BASE_DIR,
    "US-Stock-Symbols",
    "all",
    "all_tickers.txt",
)

def basic_fitering(start_date_time, end_date_time, date_dir):
    print("---------------basic filtering start-------------------")
    # 주식 목록 (필요시 Nasdaq 주식 목록을 사용)
    stock_df = pd.read_csv(
        stock_symbols_path,
        header=None,
        names=["Symbol"],
    )
    stock_list = stock_df["Symbol"].unique().tolist()
    filtered_stocks = basic_filter.filter_stocks_concurrently(
        stock_list, start_date_time, end_date_time
    )
    filtered_df = pd.DataFrame(filtered_stocks, columns=["Ticker"])
    filtered_df.to_csv(f"{date_dir}/filtered_stocks.csv", index=False)

    print("---------------basic filtering end-------------------")


def calculate_volume_score(start_date_time, end_date_time, date_dir):
    print("---------------relative volume score filtering start---------------")
    filtered_df = pd.read_csv(f"{date_dir}/filtered_stocks.csv")
    filtered_stocks = filtered_df["Ticker"].tolist()
    volume_scores = relative_volume_score.filter_stocks_concurrently(
        filtered_stocks, start_date_time, end_date_time
    )
    sorted_volume_scores = sorted(volume_scores, key=lambda x: x[1], reverse=True)
    top_40_stocks = sorted_volume_scores[:40]
    sorted_df = pd.DataFrame(top_40_stocks, columns=["Ticker", "Volume Ratio"])
    sorted_df.to_csv(f"{date_dir}/volume_ratio_score.csv", index=False)

    print("---------------relative volume score filtering end---------------")


def calculate_daily_return(start_date_time, end_date_time, date_dir):
    # print("-----------------calculate return start---------------------")
    sorted_df = pd.read_csv(f"{date_dir}/volume_ratio_score.csv")
    sorted_stocks = sorted_df["Ticker"].tolist()
    results = daily_return.calculate_return_concurrently(
        sorted_stocks, start_date_time, end_date_time
    )
    results_df = pd.DataFrame(results, columns=["Ticker", "Daily Return"])
    head_20_results_df = results_df.head(20)
    mean = (head_20_results_df["Daily Return"] > 0).mean()
    mean_string = f"Hit Ratio: {(mean):.2%}"
    average_return = head_20_results_df["Daily Return"].mean()
    average_return_string = f"Daily Total Return: {average_return:.2%}"
    head_20_results_df["Daily Return"] = head_20_results_df["Daily Return"].apply(
        lambda x: f"{x * 100:.2f}%"
    )
    head_20_results_df.to_csv(f"{date_dir}/daily_return.csv", index=False)
    result = {"Hit Ratio": [mean], "Daily Total Return": [average_return]}
    result_df = pd.DataFrame(result)
    result_df.to_csv(f"{date_dir}/result.csv", index=False)
    # print(head_20_results_df)
    print(mean_string)
    print(average_return_string)
    return (mean, average_return)


def main():
    parser = argparse.ArgumentParser(
        description="Backtest Opening Range Breakout Strategy"
    )
    parser.add_argument(
        "--start_date", required=True, help="백테스트 시작 날짜 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end_date", required=True, help="백테스트 종료 날짜 (YYYY-MM-DD)"
    )
    args = parser.parse_args()

    current_dir = os.getcwd()
    gen_data_dir = os.path.join(BASE_DIR, "gen_data")
    os.makedirs(gen_data_dir, exist_ok=True)

    # 입력받은 시작 및 종료 날짜를 datetime 객체로 변환
    temp_start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    temp_end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()

    # 월-금
    business_days = pd.bdate_range(start=temp_start_date, end=temp_end_date)
    assert (
        not business_days.empty
    ), "There are no business days between start date and end date."

    # 미국 공휴일 캘린더 설정
    us_calendar = USFederalHolidayCalendar()

    custom_business_day = pd.offsets.CustomBusinessDay(n=-14, calendar=us_calendar)

    if (
        os.path.isdir(os.path.join(gen_data_dir, temp_start_date.strftime("%Y-%m-%d")))
        is False
    ):
        today = datetime.now(eastern)
        today = today.replace(tzinfo=None)
        temp_date_14_business_days_ago = (
            pd.to_datetime(temp_start_date) + custom_business_day
        ).to_pydatetime()
        diff_days = (today - temp_date_14_business_days_ago).days
        assert (
            diff_days <= 60
        ), f"Error: The date is {diff_days} days before today, which exceeds 60 days."

    us_holidays = us_calendar.holidays(start=temp_start_date, end=temp_end_date)

    # 장 활성화 일
    trading_days = business_days.difference(us_holidays)
    trading_days_list = trading_days.to_pydatetime().tolist()

    hit_ratio_list = []
    daily_return_list = []

    for trading_day in trading_days_list:
        only_date = trading_day.strftime("%Y-%m-%d")
        date_dir = os.path.join(gen_data_dir, only_date)
        os.makedirs(date_dir, exist_ok=True)
        start_date_time = datetime.combine(trading_day, time.min)
        end_date_time = datetime.combine(trading_day, time.max)

        if os.path.isfile(f"{date_dir}/filtered_stocks.csv") is False:
            basic_fitering(start_date_time, end_date_time, date_dir)

        if os.path.isfile(f"{date_dir}/volume_ratio_score.csv") is False:
            date_14_business_days_ago = (
                pd.to_datetime(start_date_time) + custom_business_day
            )
            calculate_volume_score(date_14_business_days_ago, end_date_time, date_dir)

        print(only_date)
        (hit_ratio, daily_return) = calculate_daily_return(
            start_date_time, end_date_time, date_dir
        )
        hit_ratio_list.append(hit_ratio)
        daily_return_list.append(daily_return)

    cumulative_daily_return = (1 + pd.Series(daily_return_list)).prod() - 1
    print(f"--{args.start_date} ~ {args.end_date} Statistic--")
    print(
        f"Invidiual Stock Hit Ratio Mean: {(sum(hit_ratio_list) / len(hit_ratio_list)):.2%}"  # noqa: E501
    )
    print(f"Daily Return Mean: {(sum(daily_return_list) / len(daily_return_list)):.2%}")
    print(
        f"Positive Daily Return Ratio: {(sum(1 for x in daily_return_list if x > 0) / len(daily_return_list)):.2%}"  # noqa: E501
    )
    print(f"Cumulative Daily Return: {cumulative_daily_return * 100:.2f}%")


if __name__ == "__main__":
    main()
