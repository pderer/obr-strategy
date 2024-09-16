import unittest
from datetime import datetime, time

from returncalc import daily_return


class ReturnCalcTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._stock_list = ["GEHC"]
        temp_start_date = datetime.strptime("2024-09-13", "%Y-%m-%d").date()
        cls._start_date_time = datetime.combine(temp_start_date, time.min)
        temp_end_date = datetime.strptime("2024-09-13", "%Y-%m-%d").date()
        cls._end_date_time = datetime.combine(temp_end_date, time.max)

    def test_daily_return(self):
        daily_return_list = daily_return.calculate_return_concurrently(
            self._stock_list, self._start_date_time, self._end_date_time
        )
        # print(daily_return_list)
