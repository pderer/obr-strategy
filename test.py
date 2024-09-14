import yfinance as yf  # type: ignore

stock_list = ["GOOG", "TSLA"]


def get_stock(ticker):
    stock = yf.Ticker(ticker)

    data = stock.history(period="1d", interval="5m")
    print(data)


for stock in stock_list:
    get_stock(stock)
