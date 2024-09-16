import unittest
from datetime import datetime, time

from filters import basic_filter, relative_volume_score


class FilterTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._stock_list = ["GEHC"]
        temp_start_date = datetime.strptime("2024-09-13", "%Y-%m-%d").date()
        cls._start_date_time = datetime.combine(temp_start_date, time.min)
        temp_end_date = datetime.strptime("2024-09-13", "%Y-%m-%d").date()
        cls._end_date_time = datetime.combine(temp_end_date, time.max)

    def test_basic_filter(self):
        filtered_stocks = basic_filter.filter_stocks_concurrently(
            self._stock_list, self._start_date_time, self._end_date_time
        )
        # print(filtered_stocks)

    def test_relative_volume_score(self):
        score_list = relative_volume_score.filter_stocks_concurrently(
            self._stock_list, self._start_date_time, self._end_date_time
        )
        # print(score_list)
