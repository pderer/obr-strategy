import argparse
import datetime as dt
import os

import pandas as pd

from filters import (  # type: ignore  # noqa: F401
    basic_filter,
    relative_volume_score,
)
from returncalc import daily_return  # noqa: F401

# 주식 목록 (필요시 Nasdaq 주식 목록을 사용)
stock_df = pd.read_csv(
    "/Users/pderer/trading/dev/US-Stock-Symbols/all/all_tickers.txt",
    header=None,
    names=["Symbol"],
)
stock_list = stock_df["Symbol"].unique().tolist()


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

    # 입력받은 시작 및 종료 날짜를 datetime 객체로 변환
    start_date = dt.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date()
    current_dir = os.getcwd()
    gen_data_dir = os.path.join(current_dir, "gen_data")
    os.makedirs(gen_data_dir, exist_ok=True)

    # 현재 날짜와 시간을 기반으로 디렉토리 이름 생성
    date_range_dir_name = f"{start_date}~{end_date}"
    date_range_dir = os.path.join(gen_data_dir, date_range_dir_name)
    os.makedirs(date_range_dir, exist_ok=True)

    print("---------------basic filtering start-------------------")
    filtered_stocks = basic_filter.filter_stocks_concurrently(stock_list)
    filtered_df = pd.DataFrame(filtered_stocks, columns=["Ticker"])
    filtered_df.to_csv(f"{date_range_dir}/filtered_stocks_by_ray.csv", index=False)
    print("---------------basic filtering end-------------------")
    print("---------------relative volume score filtering start---------------")
    volume_scores = relative_volume_score.filter_stocks_concurrently(date_range_dir)
    sorted_volume_scores = sorted(volume_scores, key=lambda x: x[1], reverse=True)
    top_40_stocks = sorted_volume_scores[:40]
    sorted_df = pd.DataFrame(top_40_stocks, columns=["Ticker", "Volume Ratio"])
    sorted_df.to_csv(f"{date_range_dir}/volume_ratio_score.csv", index=False)
    print("---------------relative volume score filtering end---------------")
    print("-----------------calculate return start---------------------")
    results = daily_return.calculate_return_concurrently(date_range_dir, start_date)
    results_df = pd.DataFrame(results, columns=["Ticker", "Daily Return"])
    head_20_results_df = results_df.head(20)
    print(head_20_results_df)
    print(f"Hit Ratio: {((head_20_results_df['Daily Return'] > 0).mean()):.2%}")
    average_return = head_20_results_df["Daily Return"].sum()
    print(f"Daily Total Return: {average_return:.2%}")


# Ray 종료 및 실행
if __name__ == "__main__":
    main()
