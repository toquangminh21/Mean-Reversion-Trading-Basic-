import yfinance as yf
import pandas as pd

class SMA20:

    def __init__(self,ticker,is_long=False,is_short=False) -> None:
        if not get_type_check({ticker:str,is_long:bool,is_short:bool}):
            raise TypeError("Type mismatch during instantiation of Algo class")
        self.ticker = ticker
        self.is_long = is_long
        self.is_short = is_short
        
    def get_ticker(self):
        ''' Provides the ticker symbol of the asset 
            
            :returns: The string representation of the SMA20 instance's ticker
            :rtype: str 

        '''
        return self.ticker

    def run_algo(self,start,stop):
        ''' Changes booleans is_long and is_short by propogating SMA20 trading algorithm 
            
            :param start: Starting date 
            :type start: str
            :param stop: Stopping date
            :type stop: str
            :returns: None 
            :rtype: None

        '''
        # TODO: testing suite must include index error issues...
        # TODO: ...raise exception if is_long and is_short are both true

        if not get_type_check({start:str,stop:str}):
            raise TypeError("Type mismatch during execution of run_algo")

        ticker_hist = yf.Ticker(self.get_ticker()).history(period="max") 
        start_Timestamp = pd.Timestamp(start)  
        stop_Timestamp = pd.Timestamp(stop)
        cur_Timestamp = start_Timestamp

        if start_Timestamp < ticker_hist.index[0]:
            raise ValueError("Simple moving average of ticker " + self.get_ticker + " was evaluated at invalid range" + str(start_Timestamp))     
        
        # * Following line will change the start in the event of a market closure, etc.    
        while start_Timestamp not in ticker_hist.index:
            start_Timestamp = start_Timestamp - pd.Timedelta('1 days')
        start_hist_idx = ticker_hist.index.get_loc(start_Timestamp) 
        stop_hist_idx = ticker_hist.index.get_loc(stop_Timestamp)

        # ? Would it be more appropriate to stop at stop_hist_idx + 1?
        for idx in range(start_hist_idx, stop_hist_idx):
            if ticker_hist.iloc[idx,3] > self.get_simple_moving_average(str(cur_Timestamp)): 
                self.short = True
                self.long = False
            else: 
                self.short = False
                self.long = True

            cur_Timestamp = ticker_hist.index[idx] 

    def get_long(self):
        ''' States if asset position is long 

            :returns: True if Long, False otherwise
            :rtype: bool 

        '''
        return self.is_long

    def get_short(self):
        ''' States if asset position is short 

            :returns: True if Short, False otherwise 
            :rtype: bool 

        '''
        return self.is_short

    def get_simple_moving_average(self,start):
        '''  
            :param start: Starting date 
            :type start: str
            :returns: 20 day simple moving average of the asset 
            :rtype: bool 

        '''
        # TODO: testing suite must include index error issues, errors must be handeled as appropriate
        
        if not get_type_check({start:str}):
            raise TypeError("Type mismatch during calculation of SMA20")
        ticker_hist = yf.Ticker(self.get_ticker()).history(period="max") 
        start_Timestamp = pd.Timestamp(start) 

        # ! The following line assumes that ticker_hist has at least one data entry in the dataframe
        if start_Timestamp < ticker_hist.index[0]:
            raise ValueError("Simple moving average of ticker " + self.get_ticker + " was evaluated at invalid range" + str(start_Timestamp)) 

        # * Following line checks for market closures    
        while start_Timestamp not in ticker_hist.index:
            start_Timestamp = start_Timestamp - pd.Timedelta('1 days')
        
        start_hist_idx = ticker_hist.index.get_loc(start_Timestamp)

        if start_hist_idx > 19:
            return sum(list(ticker_hist.iloc[start_hist_idx-19:start_hist_idx+1,3]))/20
        else:
            len_remaining = len(list(ticker_hist.iloc[0:start_hist_idx+1,3])) 
            return sum(list(ticker_hist.iloc[0:start_hist_idx+1,3]))/len_remaining


def get_type_check(param_type_dictionary):
    '''
        :param param_type_dictionary: a dictionary for all method or function paramaters with the paramater as the key...
        ...and the intended type of the paramater as the value
        :type param_type_dictionary: dict
        :returns: True if all paramaters match their required type
        :rtype: bool

    '''
    for param in list(param_type_dictionary.keys()):
        if not isinstance(param, param_type_dictionary[param]):
            return False
    return True

if __name__ == "__main__":
    import timeit

    def main():
        SMA20('MSFT').run_algo('2018-3-18','2018-4-18')
    main()