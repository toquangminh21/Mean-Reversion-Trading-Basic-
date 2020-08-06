import numpy as np
import pandas as pd
import yfinance as yf


class BollingerBands:
    """
    Note for development team:
    When back testing, you will run run_algo() first, then use the is_long and is_short as inputs
    to your functions.
    When performing backtest on historical data:
        update the self.price_data each time in your loop before running run_algo()
        the price_data should be an array of closing price data, with (desired window + 2) days
        (desired window should set to 20 for now. So 22 days of closing price data)
        the last data point in the array should be "today"
    When performing backtest on real-time data:
        update the self.price_data using the get_current_data() function first.
    """

    def __init__(self, ticker):
        """
        Initialize class attributes
        :param ticker: A ticker name
        :return: Void
        :rtype: Void
        """

        self.ticker = ticker
        self.price_data = pd.Series(data=[0])  # array of closing price data, with (desired window + 2) days
        self.is_long = False
        self.is_short = False
        self.entry = 0
        self.highest = -10000
        self.lowest = 10000
        self.total_price_data = yf.download(tickers=self.ticker,interval = "1d",    )

    def get_current_data(self, period, day=None):
        """
        Get historical stock price data with given ticker name and time horizon
        :return: Historical close price
        :rtype: pandas.core.series.Series
        """
        data = None

        #! While the period is provided to this code, it isn't actually used because...
        #! ...the new methods with downloading use a 22 day timedelta.
        #! This must be fixed in future versions 

        if day is not None:
            end_stamp = pd.Timestamp(day)
            start_index = self.total_price_data.index.get_loc(end_stamp) - 21
            start_stamp = self.total_price_data.index[start_index] 
            data = self.total_price_data.loc[start_stamp:end_stamp]

        else:
            interval = "1d"
            data = yf.download(tickers=self.ticker, period=period, interval=interval,    )
        
        self.price_data = data["Close"]
        
    def cal_moving_avg(self, start, end):
        """
        Calculate the bollinger band numbers
        :param start : If calculating today's sma, start = 1, if yesterday, start = 0
        :param end : If calculating today's sma, end = -1, if yesterday, end = -2
        :return: The five bollinger band parameters
        :rtype: float
        """

        sma = self.price_data.iloc[start:end].mean()
        std = self.price_data.iloc[start:end].std()

        upper1 = sma + std
        upper2 = sma + 2*std
        lower1 = sma - std
        lower2 = sma - 2*std

        return sma, upper1, upper2, lower1, lower2

    def run_algo(self, day=None):
        """
        Implement the Bollinger Bands trading strategy
        :return: void
        :rtype: void
        """
        # TODO: We will need to have a way to modify what "today" means ...
        # TODO ... likely through the means of an optional paramater

        # Get the historical data
        # if test on real-time data

        # If test the historical performance,
        # update the self.price_data as a moving 22-days closing price data array each time.
        self.get_current_data("22d", day=day)

        # Get today and yesterday's close price
        today = self.price_data.iloc[-1]
        yesterday = self.price_data.iloc[-2]

        # Calculate standard moving average, past volatility and bollinger bands
        # Yesterday's bollinger band
        y_sma, y_upper1, y_upper2, y_lower1, y_lower2 = self.cal_moving_avg(0, -2)
        # Today's bollinger band
        t_sma, t_upper1, t_upper2, t_lower1, t_lower2 = self.cal_moving_avg(1, -1)

        # ENTRY LOGIC

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

        # EXIT LOGIC

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

    def get_ticker(self):
        """
        Get the ticker name
        :return: The ticker name
        ":rtype: str
        """
        return self.ticker

    def get_long(self):
        """
         Get whether the portfolio is longing the asset
         :return: whether the portfolio is longing the asset
         ":rtype: bool
         """
        return self.is_long

    def get_short(self):
        """
         Get whether the portfolio is shorting the asset
         :return: whether the portfolio is shorting the asset
         ":rtype: bool
         """
        return self.is_short

    def set_long(self):
        """
         Set the status as longing the asset
         :return: void
         ":rtype: void
         """
        self.is_long = True

    def set_short(self):
        """
         Set the status as shorting the asset
         :return: void
         ":rtype: void
         """
        self.is_short = True

if __name__ == "__main__":

    #Ticker data from https://dumbstockapi.com 
    import csv
    tickerCSVfile = open('/Users/iain/Documents/ENCF/Programming/backtest-framework/dumbstockapi.csv')
    tickerReader = csv.reader(tickerCSVfile)
    tickerData = list(tickerReader)
    tickerCSVfile.close()

    #* Remoging the heder and focusuing on the tickers themselves in this listcomp
    tickers = [i[0] for i in tickerData if i[0] != 'ticker']

    #! This will terminate at ticker symbol "EAI", as there is over a year between...
    #! ...The most recent day of trading and the second most recent day of trading...
    #! ...this is not a likely case for when we will be carrying out backtesting...
    #! ...so I am not overly concerned
    
    for ticker in tickers:
        try:
            A = BollingerBands(ticker) 
            A.get_current_data("22d")
            depreciated_data = A.price_data
            A.get_current_data("22d", day=pd.to_datetime('2020-06-26')) 
            current_data = A.price_data
            assert(str(depreciated_data) == str(current_data))
        except AssertionError:
            current_data.to_csv("current.csv")
            depreciated_data.to_csv("depreceiated.csv")
            raise AssertionError
        except:
            print("Non-assertion error on ticker: " + str(ticker))
