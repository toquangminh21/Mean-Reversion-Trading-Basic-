from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
import yfinance as yf
from typing import Iterator


class Algo(ABC):

    def __init__(self, ticker: str):
        '''

            :param ticker: Ticker of the asset being backtested 
            :type ticker: str
            :return: No return 
            :rtype: None
        
        '''
        self.ticker = ticker
        self.price_data = pd.Series(data=[0]) 
        self.is_long = False
        self.is_short = False
        self.entry = 0
        self.total_price_data = yf.download(tickers=self.ticker,interval = "1d")
        self.set_highest()
        self.set_lowest()

    #? Were we to institute strict typing, would the follwing line be syntaticaly correct?
    def get_current_data(self, period, day=None) -> None:
        '''
        
            Get 22 day stock price data with given ticker name and time horizon
            
            :param period: String identifying period of data being requested, such as "22d" for 22 days 
            :type period:  str
            :param day: Final day of data collection
            :type day:
            :type day: If provided, str, otherwise None 
            :return: No return
            :rtype: None
        
        '''
        data = None
        if day is not None:
            end_stamp = pd.Timestamp(day)
            start_index = self.total_price_data.index.get_loc(end_stamp) - 21
            start_stamp = self.total_price_data.index[start_index] 
            data = self.total_price_data.loc[start_stamp:end_stamp]
        else:
            interval = "1d"
            data = yf.download(tickers=self.ticker, period=period, interval=interval)
        self.price_data = data["Close"]

    @abstractmethod
    def run_algo(self) -> None:
        pass

    @abstractmethod
    def set_highest(self) -> None:
        pass

    @abstractmethod
    def set_lowest(self) -> None:
        pass

    @abstractmethod
    def __name__(self) -> None:
        pass

    def get_ticker(self) -> str:
        '''

            Get the ticker name

            :return: The ticker name
            :rtype: str
        
        '''
        return self.ticker

    def get_long(self) -> bool:
        '''

            Retreives if portfolio is longing the asset

            :return: whether the portfolio is longing the asset
            :rtype: bool
        
        '''
        return self.is_long

    def get_short(self) -> bool:
        '''

            Retreives if portfolio is longing the asset

            :return: whether the portfolio is longing the asset
            :rtype: bool
        
        '''
        return self.is_short

    def __set_long(self) -> None:
        '''

            Set the Algo state to long
            
            :return: void
            :rtype: void
        
        '''
        self.is_long = True

    def __set_short(self) -> None:
        '''
        
            Sets the Algo state to short

            :return: void
            :rtype: void
        
        '''
        self.is_short = True

class MinhsAlgo(Algo):
    def set_highest(self) -> None:
        self.highest = -10000

    def set_lowest(self) -> None:
        self.lowest = 10000

    def __name__(self) -> None:
        return "BollingerBands"

    def run_algo(self, day=None) -> None:
        '''

            Implement my mean reversion trading algorithm
            :return: void
            :rtype: void

        '''

        try:
            # The historical data of the stock is stored in the self.total_price_data attribute. type: pd.self.total_price_data
            
            # Create a new column to hold our 90 day rolling stdev
            self.total_price_data['Stdev'] = self.total_price_data['Close'].rolling(window=90).std()

            # Create a new column to hold our 20 day moving average
            self.total_price_data['Moving Average'] = self.total_price_data['Close'].rolling(window=20).mean()

            # Buy: 1st signal
            self.total_price_data['Buy1'] = (self.total_price_data['Open'] - self.total_price_data['Low'].shift(1)) < -self.total_price_data['Stdev']

            # Buy: 2nd signal
            self.total_price_data['Buy2'] = self.total_price_data['Open'] > self.total_price_data['Moving Average']

            # Column to indicate if buy
            self.total_price_data['BUY'] = self.total_price_data['Buy1'] & self.total_price_data['Buy2']

            # Sell: 1st signal
            self.total_price_data['Sell1'] = (self.total_price_data['Open'] - self.total_price_data['High'].shift(1)) > self.total_price_data['Stdev']

            # Sell: 2nd signal
            self.total_price_data['Sell2'] = self.total_price_data['Open'] < self.total_price_data['Moving Average']

            # Column to indicate if sell
            self.total_price_data['SELL'] = self.total_price_data['Sell1'] & self.total_price_data['Sell2']

            # Calculate daily % return series for stock
            self.total_price_data['Pct Change'] = (self.total_price_data['Close'] - self.total_price_data['Open']) / self.total_price_data['Open']

            # Calculate the strategy's return series by using the daily stock returns mutliplied by 1 if we are long and -1 if we are short
            self.total_price_data['Rets'] = np.where(self.total_price_data['BUY'], self.total_price_data['Pct Change'], 0)
            self.total_price_data['Rets'] = np.where(self.total_price_data['SELL'], -self.total_price_data['Pct Change'], self.total_price_data['Rets'])

        except Exception as err:
            print(err)

class BollingerBands(Algo):

    def set_highest(self) -> None:
        self.highest = -10000

    def set_lowest(self) -> None:
        self.lowest = 10000

    def __name__(self) -> None:
        return "BollingerBands"

    def cal_moving_avg(self, start, end) -> tuple:
        '''

            Calculate the bollinger band numbers

            :param start : If calculating today's sma, start = 1, if yesterday, start = 0
            :type start: str
            :param end : If calculating today's sma, end = -1, if yesterday, end = -2
            :type end: str
            :return: The five bollinger band parameters
            :rtype: tuple[float]
        
        '''
        sma = self.price_data.iloc[start:end].mean()
        std = self.price_data.iloc[start:end].std()

        upper1 = sma + std
        upper2 = sma + 2*std
        lower1 = sma - std
        lower2 = sma - 2*std

        return sma, upper1, upper2, lower1, lower2

    def run_algo(self, day=None) -> None:
        '''
        
            Implement the Bollinger Bands trading strategy
            :param day: Day of starting algorithm
            :type day: If provided, str, otherwise None
            :return: void
            :rtype: void
        
        '''
        self.get_current_data("22d", day=day)
        today = self.price_data.iloc[-1]
        yesterday = self.price_data.iloc[-2]

        # Calculate standard moving average, past volatility and bollinger bands
        # Yesterday's bollinger band
        y_sma, y_upper1, y_upper2, y_lower1, y_lower2 = self.cal_moving_avg(0, -2)
        # Today's bollinger band
        t_sma, t_upper1, t_upper2, t_lower1, t_lower2 = self.cal_moving_avg(1, -1)

        # If current close is in between upper and lower bollinger band (ABOVE SMA)
        # and previous close was below lower band and above sma, create position
        if (today <= t_upper2) and (today >= t_upper1) and (yesterday <= y_upper1) and (yesterday >= y_sma):
            if not self.get_long():
                self.is_long = True
                self.is_short = False
                self.entry = today

        # If current close in between upper and lower bollinger band (BELOW SMA)
        # and previous close was above lower band and below sma, create position
        if (today <= t_lower1) and (today >= t_lower2) and (yesterday <= y_sma) and (yesterday >= y_lower1):
            if not self.get_short():
                self.is_short = True
                self.is_long = False
                self.entry = today

        # Exit logic when longing the asset
        if self.get_long():
            self.highest = np.maximum(self.highest, today)
            # Stop loss
            if self.entry - today >= 0.001:
                self.is_long = False
                self.highest = -10000
            # Keep profit 10 pip trailing-stop when reaching the second upper band
            if (self.highest - today >= 0.001) and (self.highest >= t_upper2):
                self.is_long = False
                self.highest = -10000

        # Exit logic when shorting the asset
        if self.get_short():
            self.lowest = np.minimum(self.lowest, today)
            # Stopping loss
            if today - self.entry >= 0.001:
                self.is_short = False
                self.lowest = 10000
            # Keep profit 10 pip trailing-stop when reaching the second lower band
            if (today - self.lowest >= 0.001) and (self.lowest <= t_lower2):
                self.is_short = False
                self.lowest = 10000

if __name__ == "__main__":
    BollingerBands("MSFT")
