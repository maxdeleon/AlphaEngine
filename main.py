from execution import alpha
from logic import algoManager
from logic.algoManager import Strategy
from market_data import yahooClient
import random

'''
Created by Maximo Xavier DeLeon on 6/23/2021
'''

# create trading algos by utilizing inheritance
class dummyBuyStrategy(Strategy):
    def __init__(self):
        Strategy.__init__(self)

    def process_1(self):
        flip = random.randint(1, 2)
        aapl_close = self.asset_dictionary['AAPL'].close # get the current close price of apple stock
        msft_close = self.asset_dictionary['MSFT'].close  # get the current close price of microsoft stock
        if flip == 1 and aapl_close <= self.trade_cash: # if there is enough cash to buy a share of apple then buy it
            self.trade('AAPL',1,aapl_close)
            print(self.current_date,'purchased', 'aapl,', 'remaining cash:', self.cash)

        elif flip == 2 and msft_close <= self.trade_cash:
            self.trade('MSFT', 1, msft_close)
            print(self.current_date,'purchased', 'msft,', 'remaining cash:', self.cash)
        else:
            print('cash',self.cash)

    # more strategy goes here if its beefy
    def process_2(self):
        pass
    # and more strategy code goes here if your strategy is really beefy
    def process_3(self):
        pass

def main():
    TICKER_LIST = ['AAPL','MSFT']  # define the ticker to trade
    START_STOP_DATES = ('2020-6-15', '2021-6-15')  # define the start and stop dates

    # get the data
    backtest_data = yahooClient.get_close_prices_yahoo(tickers=TICKER_LIST, # tickers
                                                       start_date=START_STOP_DATES[0], # start
                                                       stop_date=START_STOP_DATES[1]) # stop
    dummy_strategy = dummyBuyStrategy() # define the strategy that will beat the sp500
    engine = alpha.Engine() # define the engine that will test our epic win strat

    engine.backtest(strategy=dummy_strategy, # tell the engine what strategy we want to backtest
                    data_dict=backtest_data, # tell the engine what data we want to backtest on
                    starting_cash=25000,# set the starting cash
                    log=True,
                    filename='BACKTEST_LOG.csv')


if __name__ == '__main__':
    main()

