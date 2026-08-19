# Opening Range Breakout (ORB) Backtester

A Python backtesting implementation of the **5-minute Opening Range Breakout (ORB)** strategy for U.S. equities.

This project is inspired by the research paper:

> **A Profitable Day Trading Strategy For The U.S. Equity Market**
> Carlo Zarattini, Andrea Barbon, Andrew Aziz
> SSRN 4729284

The backtester filters liquid and volatile U.S. stocks, ranks them using relative opening volume, and evaluates a 5-minute ORB strategy.

## Strategy Overview

### 1. Stock Filtering

Stocks must satisfy the following conditions:

* Stock price ≥ **$5**
* 14-day average daily volume ≥ **1,000,000 shares**
* 14-day ATR ≥ **$0.50**

### 2. Relative Volume Ranking

For each stock, the relative opening volume is calculated as:

```text
Relative Volume =
Current day's first 5-minute volume
-----------------------------------
Average first 5-minute volume over the previous 14 trading days
```

Stocks are ranked by this score, and the top candidates are selected for the ORB strategy.

### 3. Opening Range Breakout

The first **5-minute candle** defines the opening range.

#### Long

If the first 5-minute candle is bullish:

```text
Entry: Break above the first 5-minute high
Stop Loss: Entry Price - 10% of 14-day ATR
Exit: Market close
```

#### Short

If the first 5-minute candle is bearish:

```text
Entry: Break below the first 5-minute low
Stop Loss: Entry Price + 10% of 14-day ATR
Exit: Market close
```

The daily portfolio return is calculated using the top 20 valid candidates.

## Project Structure

```text
obr-strategy/
├── backtest.py
├── filters/
│   ├── basic_filter.py
│   └── relative_volume_score.py
├── returncalc/
│   └── daily_return.py
├── tests/
└── gen_data/
```

## Installation

Clone the repository:

```bash
git clone https://github.com/pderer/obr-strategy.git
cd obr-strategy
```

Clone the U.S. stock symbol repository:

```bash
git clone https://github.com/rreichel3/US-Stock-Symbols.git
```

Install dependencies:

```bash
pip install pandas numpy yfinance pytz
```

## Usage

Display available options:

```bash
python backtest.py -h
```

Run a backtest:

```bash
python backtest.py \
    --start_date <START_DATE> \
    --end_date <END_DATE>
```

For example:

```bash
python backtest.py \
    --start_date 2026-08-18 \
    --end_date 2026-08-18
```

Dates must use the `YYYY-MM-DD` format.

Because the backtester uses 5-minute historical data from Yahoo Finance, the current implementation is intended for relatively recent dates.

## Output

Backtest results are stored under:

```text
gen_data/
└── YYYY-MM-DD/
    ├── filtered_stocks.csv
    ├── volume_ratio_score.csv
    ├── daily_return.csv
    └── result.csv
```

The console also prints summary statistics such as:

```text
Individual Stock Hit Ratio Mean
Daily Return Mean
Positive Daily Return Ratio
Cumulative Daily Return
```

## Disclaimer

This project is intended for **research and educational purposes only**.

Backtest results do not guarantee future performance and should not be considered financial advice.
