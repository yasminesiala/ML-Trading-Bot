from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from datetime import datetime
from alpaca_trade_api import REST
from pandas import Timedelta
from finbert_utils import estimate_sentiment

API_KEY = "PK4O3YM2V1LRIMXRIX92"
API_SECRET = "b9OgNSMwwQF6bQrLHUrRcpBMieWp5KETA6FZpxRP"
BASE_URL = "https://paper-api.alpaca.markets/v2"

ALPACA_CREDS = {
    "API_KEY": API_KEY,
    "API_SECRET": API_SECRET,
    "PAPER": True
}

class MLTrader(Strategy):
    def initialize(self, symbol: str = "SPY", cash_at_risk: float = 0.5):
        self.symbol = symbol
        self.sleeptime = "24H"
        self.last_trade = None
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)

    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.symbol)
        
        if cash is None or cash <= 0 or last_price is None or last_price <= 0:
            self.log_message(f"Invalid data in position sizing - Cash: {cash}, Last Price: {last_price}")
            return 0, 0, 0
        
        quantity = max(round(cash * self.cash_at_risk / last_price, 0), 1)
        self.log_message(f"Position sizing - Cash: {cash}, Last Price: {last_price}, Quantity: {quantity}")
        return cash, last_price, quantity

    def get_dates(self):
        today = self.get_datetime()
        three_days_prior = today - Timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')

    def get_sentiment(self):
        today, three_days_prior = self.get_dates()
        try:
            news = self.api.get_news(symbol=self.symbol, start=three_days_prior, end=today)
            if not news:
                self.log_message("No news returned, skipping sentiment analysis.")
                return 0, "neutral"
            
            headlines = [ev.__dict__["_raw"]["headline"] for ev in news]
            self.log_message(f"Sentiment Analysis Headlines: {headlines}")
            probability, sentiment = estimate_sentiment(headlines)
            self.log_message(f"Sentiment Analysis - Probability: {probability}, Sentiment: {sentiment}")
            return probability, sentiment
        except Exception as e:
            self.log_message(f"Error in get_sentiment: {e}")
            return 0, "neutral"

    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()
        probability, sentiment = self.get_sentiment()

        # Print critical values for debugging
        self.log_message(f"Debug - Cash: {cash}, Last Price: {last_price}, Quantity: {quantity}, Sentiment: {sentiment}, Probability: {probability}")

        # Check if there is enough cash to trade
        if cash <= last_price or quantity == 0:
            self.log_message(f"Insufficient funds or invalid quantity - Cash: {cash}, Last Price: {last_price}, Quantity: {quantity}")
            return

        # Check if order creation conditions are met
        if sentiment == "positive" and probability > 0.999:
            self.log_message(f"Positive sentiment detected: {sentiment} with probability: {probability}")

            if self.last_trade == "sell":
                positions = self.get_positions()
                if positions:
                    self.log_message(f"Current positions before sell_all: {positions}")
                    self.sell_all()
                    self.log_message(f"Positions after sell_all: {self.get_positions()}")
                else:
                    self.log_message("No positions to sell. Skipping sell_all().")

            order = self.create_order(
                self.symbol,
                quantity,
                "buy",
                type="bracket",
                take_profit_price=last_price * 1.20,
                stop_loss_price=last_price * 0.95,
            )
            if order:
                self.log_message(f"Order created successfully: {order}")
                self.submit_order(order)
                self.last_trade = "buy"
            else:
                self.log_message("Failed to create Buy Order.")
        
        elif sentiment == "negative" and probability > 0.999:
            self.log_message(f"Negative sentiment detected: {sentiment} with probability: {probability}")

            if self.last_trade == "buy":
                positions = self.get_positions()
                if positions:
                    self.log_message(f"Current positions before sell_all: {positions}")
                    self.sell_all()
                    self.log_message(f"Positions after sell_all: {self.get_positions()}")
                else:
                    self.log_message("No positions to sell. Skipping sell_all().")

            order = self.create_order(
                self.symbol,
                quantity,
                "sell",
                type="bracket",
                take_profit_price=last_price * 0.80,
                stop_loss_price=last_price * 1.05,
            )
            if order:
                self.log_message(f"Order created successfully: {order}")
                self.submit_order(order)
                self.last_trade = "sell"
            else:
                self.log_message("Failed to create Sell Order.")
        
        else:
            self.log_message(f"No trade conditions met - Probability: {probability}, Sentiment: {sentiment}")

start_date = datetime(2020, 1, 1)
end_date = datetime(2023, 12, 30)

broker = Alpaca(ALPACA_CREDS)
strategy = MLTrader(name="mlstrat", broker=broker, parameters={"symbol": "SPY", "cash_at_risk": 0.5})

strategy.backtest(
    YahooDataBacktesting,
    start_date,
    end_date,
    parameters={"symbol": "SPY", "cash_at_risk": 0.5}
)
