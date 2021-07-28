from AlphaPackage.Logic import Strategy
import math
import pickle
from AlphaPackage.MarketData import yahooClient

'''
Created by Maximo Xavier DeLeon on 7/24/2021
'''

class BuyAndHold(Strategy):
    def __init__(self):
        Strategy.__init__(self)
        self.name = 'BuyAndHold'
        self.has_initialized = False
        self.allocation_dict = dict()
        self.verbose = False
        # the remaining 20% is just cash
    def build_index(self):
        for ticker in self.asset_dictionary.keys():  # for each ticker in the universe of tickers that this algorithm can trade
            initial_price = self.asset_dictionary[ticker].bars.Close[-1]
            initial_quantity = math.floor((self.cash * self.allocation_dict[ticker])/self.asset_dictionary[ticker].bars.Close[-1])
            self.create_order(ticker, initial_quantity, initial_price)
    def process_1(self):
        if not self.has_initialized:  # check to see if this has initialized
            self.build_index()
            self.has_initialized = True
        else:
            pass

if __name__ == '__main__':
    hodl_strat = BuyAndHold()
    pickle.dump(hodl_strat, open("Benchmark.p", "wb"))

    TICKER_LIST = ['SOYB', 'UGA', 'UNG', 'CORN']  # define the ticker to trade
    START_STOP_DATES = ('2020-6-15', '2021-6-15')  # define the start and stop dates

    # get the data
    backtest_data = yahooClient.get_close_prices_yahoo(tickers=TICKER_LIST,  # tickers
                                                       start_date=START_STOP_DATES[0],  # start
                                                       stop_date=START_STOP_DATES[1])  # stop
    pickle.dump(backtest_data,open('example_backtest_data.p','wb'))
    print('complete!')