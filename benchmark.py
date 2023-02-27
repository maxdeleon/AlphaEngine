from AlphaPackage.Execution import alpha
from AlphaPackage.Logic import Strategy
from AlphaPackage.MarketData import yahooClient
import math
import os
import pandas as pd
'''
Created by Maximo Xavier DeLeon on 7/13/2021
Updated by Maximo Xavier DeLeon on 02/27/2022
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
            initial_price = self.asset_dictionary[ticker].bars.Close[-1]
            initial_quantity = math.floor((self.cash * self.allocation_dict[ticker])/self.asset_dictionary[ticker].bars.Close[-1])
            self.create_order(ticker, initial_quantity, initial_price)
    
    def process_1(self):
        if not self.has_initialized:  # check to see if this has initialized
            #self.build_index()
            self.has_initialized = True
        else:
            pass

def test_algo_class():
    print('testing strategy classes...') # tell the user what they just did
    TICKER_LIST = ['SOYB', 'UGA', 'UNG', 'CORN']  # define the ticker to trade
    START_STOP_DATES = ('2015-2-1', '2021-6-15')  # define the start and stop dates

    dataset_path = './dataset/'
    dataset_files = [f for f in os.listdir(dataset_path) if f.endswith('.csv')]
    symbols = [s.strip('.csv') for s in dataset_files]

    dataset = dict(zip(symbols, [(pd.read_csv(dataset_path+f)).tail(10) for f in dataset_files]))
    for s in symbols:
        dataset[s].columns = [c.capitalize() if c != 'timestamp' else 'date' for c in dataset[s].columns] #= pd.DataFrame(dataset[s], columns=[c.capitalize() for c in dataset[s].columns])
        dataset[s] = dataset[s].set_index('date')

    
    # get the data
    # backtest_data = yahooClient.get_close_prices_yahoo(tickers=TICKER_LIST,  # tickers
    #                                                    start_date=START_STOP_DATES[0],  # start
    #                                                    stop_date=START_STOP_DATES[1])  # stop


    allocation_dict = dict(zip(symbols,[0 for s in symbols]))
    test_benchmark = BuyAndHold(allocation_dict=allocation_dict)  # define the strategy that will beat the sp500
    engine = alpha.Engine()  # define the engine that will test our epic win strat

    pnl = engine.backtest(strategy_object=test_benchmark,  # tell the engine what strategy we want to backtest
                          backtest_series_dictionary=dataset,  # tell the engine what data we want to backtest on
                          starting_cash=25000,  # set the starting cash
                          log=True,
                          filename='BACKTEST_LOG_benchmark.csv')

    #print('PnL %:', pnl)
def main():
    test_algo_class()
    #test_stochastic()

if __name__ == '__main__':
    main()

