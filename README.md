# ML Trading Bot
This repository contains an automated machine learning–driven trading bot that uses news sentiment analysis, Lumibot, and Alpaca to execute trades or run backtests. 
The strategy pulls recent news for a given ticker, evaluates sentiment using FinBERT, and makes buy/sell decisions using probability thresholds and bracket orders.

## Overview

The ML Trading Bot is designed to:
* Use FinBERT sentiment analysis to evaluate news headlines.
* Automatically size positions based on available cash and risk percentage.
* Execute buy or sell orders based on sentiment signals.
* Use bracket orders for risk management.
* Backtest performance using historical data from Yahoo Finance.

The default configuration trades SPY and analyzes the previous three days of news data before each trading iteration.


## Project Structure

```
ML-Trading-Bot/
│
├── finbert_utils.py          # FinBERT sentiment analysis helper functions
├── tradingbot.py             # Main trading strategy and backtesting script
├── logs/                     # Logs generated while running the bot
└── README.md
```

---

## How the Strategy Works

### 1. Position Sizing

The bot determines:

* Current cash balance
* Latest market price of the target symbol
* Number of shares to buy or sell

It calculates quantity based on the configured cash-at-risk parameter (default: 0.5 or 50 percent of available cash).

### 2. Sentiment Analysis

For every trading iteration, the bot:

1. Fetches news headlines for the last three days using Alpaca’s news API.
2. Passes headlines to FinBERT through `estimate_sentiment()`.
3. Receives sentiment (positive, negative, or neutral) and a confidence probability.

The bot will only take action when:

* Sentiment is positive or negative, and
* Probability is greater than 0.999.

### 3. Trading Logic

Positive sentiment with high probability triggers a buy order.
Negative sentiment with high probability triggers a sell order.

The bot creates bracket orders that include:

* A take-profit price
* A stop-loss price

The bot also tracks the last trade direction to avoid unnecessary flips and manages open positions accordingly.

---

## Backtesting

The provided script performs a backtest using:

* YahooDataBacktesting
* Date range from January 1, 2020 to December 30, 2023
* SPY as the default trading symbol

Backtesting is triggered with:

```python
strategy.backtest(
    YahooDataBacktesting,
    start_date,
    end_date,
    parameters={"symbol": "SPY", "cash_at_risk": 0.5}
)
```

---

## Installation

### 1. Clone the Repository

```
git clone https://github.com/yasminesiala/ML-Trading-Bot.git
cd ML-Trading-Bot
```

### 2. Install Dependencies

If you have a `requirements.txt` file:

```
pip install -r requirements.txt
```

Or install manually:

```
pip install lumibot alpaca-trade-api pandas torch transformers yfinance
```

---

## API Credentials

```
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets/v2
```


## Running the Bot

### Backtesting (default)

```
python tradingbot.py
```

### Live Trading

Replace the final `backtest` call with:

```python
strategy.run()
```

Make sure your API keys are set for either paper or live trading.


## FinBERT Sentiment Model

The FinBERT model is used to classify financial text. It outputs:

* A sentiment label (positive, negative, neutral)
* A probability score for the classification

`estimate_sentiment()` in `finbert_utils.py` handles loading the model, running inference, and returning both values for decision-making.


## Logging

The bot logs:

* Position sizing calculations
* Headlines used for sentiment analysis
* Model predictions
* Orders placed
* Errors or unexpected API results

Logs are stored in the `logs/` directory and are useful for debugging.
