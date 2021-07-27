from execution import alpha
from tools import Stochastics as stoch
from logic.algoManager import Strategy
from market_data import yahooClient
import pandas as pd
import matplotlib.pyplot as plt
import math
'''
Created by Maximo Xavier DeLeon on 6/23/2021
'''

# create custom trading strategies by declaring a Strategy child class

class BuyAndHold(Strategy):
    def __init__(self):
        Strategy.__init__(self)
        self.has_initialized = False
        self.verbose = True

        # the remaining 20% is just cash
    def build_index(self):
        self.allocation_dict = {}
        partition = 1/len(self.asset_dictionary.keys())
        for ticker in self.asset_dictionary.keys():  # for each ticker in the universe of tickers that this algorithm can trade
            initial_price = self.asset_dictionary[ticker].bars.Close[0]
            initial_quantity = math.floor((self.trade_cash * partition)/initial_price)
            self.allocation_dict[ticker] = {'partition %': str(partition*100)+'%',
                                            'value':partition*self.trade_cash,
                                            'quantity':initial_quantity,
                                            'pps':initial_price}
        print('portfolio allocation set. creating orders')

        for ticker in self.asset_dictionary.keys():
            self.create_order(ticker, self.allocation_dict[ticker]['quantity'], self.allocation_dict[ticker]['pps'],message='benchmark order')





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
    test_benchmark = BuyAndHold()  # define the strategy that will beat the sp500
    engine = alpha.Engine()  # define the engine that will test our epic win strat

    engine.backtest(strategy_object=test_benchmark,  # tell the engine what strategy we want to backtest
                    backtest_series_dictionary=backtest_data,  # tell the engine what data we want to backtest on
                    starting_cash=25000,  # set the starting cash
                    log=True,
                    filename='BACKTEST_LOG.csv')


def test_stochastic(): # method to test stochastic processes
    print('testing stochastic process classes...') # tell the user what they just did
    some_asset = {'drift':.2,'volatility':.1,'delta_t':1/252,'initial_price':100} # random parameters
    asset_simulator = stoch.StochasticProcessManager(stochastic_parameters=some_asset) # create a instance of the SPM
    simulations = asset_simulator.build_scenarios(amount=100) # generate 10 different GBM simulations
    final_df = pd.DataFrame()
    for i in simulations.keys():   # print out all of the price lists
        final_df[i] = simulations[i].Close
        print(i)
        print('-=-=-=-=-==--=-=-=-')

    final_df.plot(legend=False)
    plt.title(str(some_asset), fontsize=10)
    plt.show()

def main():
    test_algo_class()
    #test_stochastic()

if __name__ == '__main__':
    main()