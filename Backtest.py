import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from mdutils import MdUtils
import uuid
import os
import six

dfRowReadTimestamp = lambda df, Timestamp: [df.loc[Timestamp, col] for col in ["Close", "Position", "Cash", "Equity", "Capital", "Volume"]] 

class Backtest:
    
    def __init__(self, algo, capital: float, years_back):
        '''
        
            :param algo: Trading algorithm being backtested or None if testing run_backtest
            :type algo: A subclass of Algo or None
            :param capital: Capital balance at the start of the backtest or None if testing run_backtest
            :type capital: float or None
            :param years_back: Years back from current date when backtests started, or None if testing run_backtest
            :type years_back: int

        '''
        #* During debugging, algo along with other paramaters are None
        if algo != None: 
            self.algo = algo
            self.ticker = self.algo.ticker
            self.years_back = years_back
            self.capital = capital
            self.initial_capital = capital

            #> Placement of closing prices into hist_positions dataframe 
            start_stamp = pd.to_datetime('today').normalize() - pd.Timedelta(years_back*365, "d")

            while True:
                try:
                    start_iloc = self.algo.total_price_data.index.get_loc(start_stamp)
                    break
                except KeyError:
                    start_stamp = start_stamp - pd.Timedelta(1,"d")

            self.hist_positions = self.algo.total_price_data[["Close"]].iloc[start_iloc:].copy()
            n = len(self.hist_positions.index)

            #> Create columns in hist_positions dataframe
            #>      Positions initalized to None
            #>      On first day of backtest all capital is stored as cash

            self.hist_positions["Position"] = [None for i in range(0,n)]
            self.hist_positions["Cash"] = [capital if i == 0 else 0 for i in range(0,n)]
            self.hist_positions["Equity"] = [0 for i in range(0,n)]
            self.hist_positions["Capital"] = [capital if i == 0 else 0 for i in range(0,n)]
            self.hist_positions["Volume"] = [0 for i in range(0,n)]
            
            #> Establish and randomly generated ID for the backtest
            self.ID = uuid.uuid4()

    def run_backtest(self,debug_filestring=None) -> None:
        ''' 

            Runs the backtest on the algorithm provided in the self.algo attribute

            :returns: Value indicating successful backtest
            :rtype: bool

        '''


        #> Instead of executing the algorithm 
        if debug_filestring != None:
            self.hist_positions = pd.read_csv(debug_filestring,index_col=0)
            self.capital = self.hist_positions.iloc[0, 4]


        prevTimestamp = self.hist_positions.index[0] 

        #> 0: Close     1: Position     2:Cash     3:Equity     4: Capital      5: Volume
        # for row in range(1, len(self.hist_positions.index)):

        for curTimestamp in self.hist_positions.index[1:]:
            prevClose, prevPosition, prevCash, prevEquity, prevCapital, prevVol  = dfRowReadTimestamp(self.hist_positions, prevTimestamp)
            curClose, curPosition, curCash, curEquity, curCapital, curVol = dfRowReadTimestamp(self.hist_positions, curTimestamp)

            #> Execution of algorithm
            if debug_filestring == None:
                self.algo.run_algo(pd.Timestamp(curTimestamp))
                if self.algo.get_long() and self.algo.get_short(): 
                    print(pd.Timestamp(curTimestamp))
                    raise ValueError("Algorithm says to go both long and short")

                if self.algo.get_long():
                    curPosition = "Long"
                elif self.algo.get_short():
                    curPosition = "Short"
                else:
                    curPosition = None

            #TODO: Use shallow coppies to avoid frequent, difficult to read 'self.hist_positions' statements 

            #> Evaulating backtest if position has changed
            if  curPosition != prevPosition:

                if  curPosition == "Long":
                    #> Step 1: Clear off previous equity, compute volume
                    curCash = prevCash + prevEquity
                    curVol = curCash // curClose

                    #> Step 2: Make Purchase
                    curCash = curCash - curClose * curVol
                    curEquity = curClose * curVol

                elif  curPosition == "Short":
                    #> Step 1: Clear off previous equity, compute volume 
                    curCash = prevCash + prevEquity
                    curVol = curCash // curClose
                    #> Step 2: Make Purchase
                    curCash = curCash + curClose * curVol
                    curEquity = -1 * curClose * curVol
                    
                else:
                    #? Does the previous position affect the current cash in the case of a current day neutral position
                    if prevPosition == "Long":
                        curCash = prevCash + curClose * prevVol
                        self.__add_to_capital((curClose - prevClose)* prevVol)
                    elif prevPosition == "Short":
                        curCash = prevCash - curClose * prevVol
                        self.__add_to_capital((prevClose - curClose)* prevVol) 

                    #> Set equity, volume to zero 
                    curEquity = 0
                    curVol = 0

            #> Evaluating backtest if position has not changed
            else:
                #* Cash Unchanged
                curCash = prevCash
                #* Volume Unchanged
                curVol = prevVol 
                
                if curPosition == "Long":
                    #* Equity is the product of share price and volume
                    curEquity = curClose * curVol
                    #* Capital grows by the difference in the product of price and volume
                    self.__add_to_capital((curClose - prevClose)* prevVol)
                elif curPosition == "Short":
                    #* Equity is the negative product of share price and volume
                    curEquity = -1 * curClose * curVol
                    #* Capital shrinks by the difference in the product of price and volume
                    self.__add_to_capital((prevClose - curClose)* prevVol)

            curCapital = self.__get_capital() 
            self.hist_positions.loc[curTimestamp, "Close"] = curClose
            self.hist_positions.loc[curTimestamp, "Position"] = curPosition
            self.hist_positions.loc[curTimestamp, "Cash"] = curCash
            self.hist_positions.loc[curTimestamp, "Equity"] = curEquity
            self.hist_positions.loc[curTimestamp, "Capital"] = curCapital
            self.hist_positions.loc[curTimestamp, "Volume"] = curVol
            prevTimestamp = curTimestamp 
            
        return True

    def __add_to_capital(self, amt: float) -> None:
        '''

            Description: Private method to increase or decrease ammount of capital

            :param amt: Ammount capital is being added to
            :type amt: float

        '''
        self.capital += amt 

    def __get_capital(self) -> float:
        '''

            Description: Private method to return the ammount of capital

            :return: current ammount of capital
            :rtype: float            

        '''
        return self.capital

    def generate_report(self) -> None:
        '''

            Description: Generates a PDF report with backtest statisitics and relevant plots 

            :return: No return
            :rtype: None 

        '''
        from pandas.plotting import register_matplotlib_converters
        register_matplotlib_converters()

        portfolio_img_filename = self._graph_portfolio()
        md_filename = 'backtest_report_{}.md'.format(self.ticker)

        control_profit_loss = self._profit_control()
        positions_taken = self._position_count()
        average_profit_loss, average_trimmed_profit_loss, kelley_criterion, sharpe_ratio = self._pl_ratios_and_kelley_and_sharpe()

        param_dict = {
            '$TICKER': self.ticker,
            '$ID': str(self.ID),
            '$ALGONAME': self.algo.__name__(),                    
            '$YEARSBACK': str(self.years_back),
            '$INITIALCAPITAL': '$' + str(round(self.initial_capital, 2)),
            '$APL': str(round(average_profit_loss, 2)) ,
            '$ATPL': str(round(average_trimmed_profit_loss, 2)),
            '$CPL': str(round(control_profit_loss, 2)),
            '$POS': str(round(positions_taken, 2)),
            '$K': str(round(kelley_criterion, 2)),
            '$RAT': str(round(sharpe_ratio, 2)),
            '$FILENAME': portfolio_img_filename
                    }        

        with open('backtest_report_template.md', 'r') as pfile:
            lines = pfile.read()
            for keys in list(param_dict.keys()):
                lines = lines.replace(keys, param_dict[keys])

        with open(md_filename,'w') as pfile:
            pfile.write(lines)
        
        os.system('mdpdf ' + md_filename)

    def _graph_portfolio(self) -> str:
        '''

            Plots capity, equity, and cash over duration of backtest

            :returns: Filestring of saved png of portfolio graph
            :rtype: str

        '''
        # TODO : put units
        
        plt.rcParams['font.sans-serif'] = "Arial"
        plt.rcParams['font.family'] = "sans-serif"

        plt.figure(figsize=(5.5,3.5))
        plt.plot(self.hist_positions.index, self.hist_positions['Capital'], label='Capital', color="#182851", linewidth=2)
        plt.plot(self.hist_positions.index, self.hist_positions['Equity'], label='Equity', color="#6D6E6F", linewidth=1)
        plt.plot(self.hist_positions.index, self.hist_positions['Cash'], label='Cash', color="#870002", linewidth=1)
        plt.xlabel('Time (YYYY-MM)')
        plt.ylabel('Dollars')
        plt.legend(loc='best')

        img_filename = 'backtest_portfolio_graph_{}.png'.format(self.ticker)
        plt.tight_layout()
        plt.savefig(img_filename)
        return img_filename
    
    def _profit_control(self) -> float:
        '''

            Computes profit in control case where asset is bought at beginning and sold at end

            :returns: Profts earned in control case
            :rtype: float

        '''
        start = self.hist_positions.iloc[0, 4]
        vol = start // self.hist_positions.iloc[1, 0]
        final = start - vol * self.hist_positions.iloc[1, 0] + vol * self.hist_positions.iloc[-1, 0]
        percentange_pl = (final - start) / start * 100
        return percentange_pl

    def _pl_ratios_and_kelley_and_sharpe(self) -> tuple:
        ''' 

            Computes P/L ratios, Kelley criterion, and Sharpe ratio

            :returns: Average P/L ratio across all trades, average P/L ratio across all non-outlier trades, kelley criterion, sharpe ratio
            :rtype: tupple[floats]

        '''
        pl = []
        position = None
        cp = -1
        for i in range(1, len(self.hist_positions.index)):
            if self.hist_positions.iloc[i, 1] != position:
                if position is None:
                    cp = self.hist_positions.iloc[i, 4]
                    position = self.hist_positions.iloc[i, 1]
                else:
                    # store the change
                    pl.append((self.hist_positions.iloc[i, 4] - cp) / cp)
                    cp = self.hist_positions.iloc[i, 4]
                    position = self.hist_positions.iloc[i, 1]
        if self.hist_positions.iloc[-1, 1] is not None:
            pl.append((self.hist_positions.iloc[-1, 4] - cp) / cp)

        pl = np.array(pl)
        avg_pl = np.mean(pl)
        std = np.std(pl)
        dist_avg_pl = np.abs(pl - avg_pl)
        trimmed = pl[dist_avg_pl < 2 * std]
        if len(trimmed) == 0:
            raise ValueError("Trimmed P/L array is empty")
        avg_trim_pl = np.mean(trimmed)

        win_prob = len(pl[pl > 0]) / len(pl)
        if len(pl[pl < 0]) == 0:
            raise ValueError("The kelley criterion is a nan in this simulation because no unprofitable trades")
        win_loss = len(pl[pl > 0]) / len(pl[pl < 0])
        kelley = win_prob - (1 - win_prob) / win_loss


        #TODO: risk_free_return is just the current 5 year treasury rate
        five_year_treasury_rate = 1 + yf.Ticker("^FVX").history().iloc[-1, 3]
        return_on_investment = (self.hist_positions.iloc[-1, 4] - self.hist_positions.iloc[0, 4]) / self.hist_positions.iloc[0, 4] * 100
        risk_free_return = five_year_treasury_rate * self.hist_positions.iloc[0, 4]
        std_close = np.std(self.hist_positions['Close'])
        sharpe_ratio = (return_on_investment - risk_free_return) / std_close

        return avg_pl, avg_trim_pl, kelley, sharpe_ratio

    def _position_count(self) -> int:
        ''' 
            
            Counts number of positions taken

            :returns: Number of positions taken
            :rtype: int
        
        '''
        position_count = 0
        position = None
        for i in range(1, len(self.hist_positions.index)):
            if self.hist_positions.iloc[i, 1] != position:
                if position is None:
                     position_count+=1
                elif position is not None and self.hist_positions.iloc[i, 1] is not None:
                     position_count+=1
                position = self.hist_positions.iloc[i, 1]
        return  position_count


if __name__ == "__main__":
    import Bollinger_Algorithm
    import Algo
    import pandas as pd
    Appl_algo = Algo.BollingerBands("AAPL")
    Appl_back = Backtest(Appl_algo, 100000, 1)
    Appl_back.run_backtest()
    Appl_back.generate_report()
