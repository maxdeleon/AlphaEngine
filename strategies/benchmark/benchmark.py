from execution import alpha
from logic import algoManager
from tools import Stochastics as stoch
from logic.algoManager import Strategy
from market_data import yahooClient
import pandas as pd
import matplotlib.pyplot as plt
import math
'''
Created by Maximo Xavier DeLeon on 7/13/2021
'''

class BuyAndHold(Strategy):
    def __init__(self,allocation_dict={},verbose=False):
        Strategy.__init__(self)
        self.has_initialized = False
        self.allocation_dict = allocation_dict
        self.verbose = False
        # the remaining 20% is just cash
    def build_index(self):
        for ticker in self.asset_dictionary.keys():  # for each ticker in the universe of tickers that this algorithm can trade
            initial_price = self.asset_dictionary[ticker].close
            initial_quantity = math.floor((self.cash * self.allocation_dict[ticker])/self.asset_dictionary[ticker].close)
            self.create_order(ticker, initial_quantity, self.asset_dictionary[ticker].close)
    def process_1(self):
        if not self.has_initialized:  # check to see if this has initialized
            self.build_index()
            self.has_initialized = True
        else:
            pass

def test_algo_class():
    print('testing strategy classes...') # tell the user what they just did
    TICKER_LIST = ['SOYB', 'UGA', 'UNG', 'CORN']  # define the ticker to trade
    START_STOP_DATES = ('2020-6-15', '2021-6-15')  # define the start and stop dates

    # get the data
    backtest_data = yahooClient.get_close_prices_yahoo(tickers=TICKER_LIST,  # tickers
                                                       start_date=START_STOP_DATES[0],  # start
                                                       stop_date=START_STOP_DATES[1])  # stop
    allocation_dict = {'SOYB': 0.2,
                       'UGA': 0.2,
                       'UNG': 0.2,
                       'CORN': 0.2}
    test_benchmark = BuyAndHold(allocation_dict=allocation_dict)  # define the strategy that will beat the sp500
    engine = alpha.Engine()  # define the engine that will test our epic win strat

    pnl = engine.backtest(strategy_object=test_benchmark,  # tell the engine what strategy we want to backtest
                    backtest_series_dictionary=backtest_data,  # tell the engine what data we want to backtest on
                    starting_cash=25000,  # set the starting cash
                    log=True,
                    filename='BACKTEST_LOG_benchmark.csv')

    print('PnL %:', pnl)
def main():
    test_algo_class()
    #test_stochastic()

if __name__ == '__main__':
    main()

