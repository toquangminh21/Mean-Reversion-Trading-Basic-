import Backtest
import pytest
import os
import pandas as pd
import random

def generate_BacktestTestingDFs(m = 10):
    '''

        Description: creates Backtest Testing CSV representaitons of data frames for test_run_backtest

    '''

    parent_filestring = os.getcwd()
    parent_DF = pd.read_csv(os.path.join(parent_filestring, "testsuite/BacktestTestingDF1.csv"),index_col=0)
    capital = 10000
    n = len(parent_DF.index)

    for j in range (2,m):
        new_DF = parent_DF
        new_DF["Position"] = [["Long", "Short", "Neutral"][random.randint(0,2)] for i in range(0,n)]
        new_DF["Close"] = [random.random()*1000 for i in range(0,n)]

        new_DF["Cash"] = [capital if i == 0 else 0 for i in range(0,n)]
        new_DF["Equity"] = [0 for i in range(0,n)]
        new_DF["Capital"] = [capital if i == 0 else 0 for i in range(0,n)]
        new_DF["Volume"] = [0 for i in range(0,n)]    
        new_DF.to_csv(os.path.join(parent_filestring, "testsuite/BacktestTestingDF" + str(j) + ".csv"), index='False')

def test_run_backtest():
    '''

        Description: pytest unit testing function

    '''
    parent_filestring = os.getcwd()
    objBacktest = Backtest.Backtest(None, None, None)

    #TODO: use Python os package to list all files rather than doing it in this "quick and dirty" way
    for i in range(1,10):

        objBacktest.run_backtest(os.path.join(parent_filestring, "testsuite/BacktestTestingDF" + str(i) + ".csv"))
        test_hist_positions = objBacktest.hist_positions
        delta = 0.000001
        
        n = len(test_hist_positions.index)
        dfRowRead = lambda df, row: [df.iloc[row,i] for i in range(0,6)] 
        equitySign = lambda Position: -1 if Position == 'Short' else 1
        test_hist_positions.to_csv('tmp.csv')

        #* Values that should be equal but are not directly coppied are compared within a tolerance

        for row in range(1, n):
            prevClose, prevPosition, prevCash, prevEquity, prevCapital, prevVol = dfRowRead(test_hist_positions, row-1)
            curClose, curPosition, curCash, curEquity, curCapital, curVol = dfRowRead(test_hist_positions,row)
            assert (curCapital - curCash - curEquity) < delta

            if curPosition != 'Short' and curPosition != 'Long':
                assert curVol == 0
                assert curEquity == 0
                if prevPosition == curPosition:
                    assert (curCapital - prevCapital) < delta

            if curPosition == prevPosition:
                assert curCash == prevCash
                assert curVol == prevVol
            
            if curPosition == 'Short' or curPosition == 'Long':
                assert curEquity == curVol * curClose * equitySign(curPosition)
                if prevPosition != 'Short' and prevPosition != 'Long':
                    assert curCapital == prevCapital
                elif prevPosition != curPosition:
                    assert (curCapital - prevCash - prevEquity) < delta

generate_BacktestTestingDFs()
test_run_backtest()