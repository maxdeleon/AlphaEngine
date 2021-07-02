import math
import numpy as np
from execution import alpha
from logic import algoManager
from logic.algoManager import Strategy
from market_data import yahooClient
import talib
from talib import MA_Type

'''
Created by Maximo Xavier DeLeon on 6/23/2021
'''

# create custom trading strategies by declaring a Strategy child class
class Bollinger(Strategy):
    def __init__(self):
        Strategy.__init__(self)
        self.set_trade_allocation(0.5) # set the amount of cash to be available for a trade at any given time

    def process_1(self):
        self.stop_limits = (0.10, -0.03)
        target_ticker = 'AAPL'
        self.close_series = self.asset_dictionary[target_ticker].bars.Close  # get the current close price of apple stock
        upper, middle, lower = talib.BBANDS(self.close_series, matype=MA_Type.T3)
        current_price = self.close_series[-1]
        position_size = math.floor(self.trade_cash/current_price)
        can_afford = True if self.trade_cash > position_size * current_price else False

        # bollinger buy
        if can_afford and current_price <= lower[-1] and position_size > 0:
            self.trade(target_ticker, position_size, current_price)
            print(self.close_series.index[-1],'upper bollinger bot',position_size)
            self.buy_price = current_price

        # bollinger sell
        elif self.asset_dictionary[target_ticker].position > 0 and current_price >= upper[-1]:
            print(self.close_series.index[-1],'lower bollinger sold',self.asset_dictionary[target_ticker].position)
            self.trade(target_ticker, -self.asset_dictionary[target_ticker].position, current_price)

        # stop loss
        elif self.asset_dictionary[target_ticker].position > 0 and np.log(current_price/self.buy_price) <= self.stop_limits[1]:
            print(self.close_series.index[-1],'stop loss sold', self.asset_dictionary[target_ticker].position)
            self.trade(target_ticker, -self.asset_dictionary[target_ticker].position, current_price)

        # offset stop
        elif self.asset_dictionary[target_ticker].position > 0 and np.log(current_price/self.buy_price) >= self.stop_limits[0]:
            print(self.close_series.index[-1],'stop win sold', self.asset_dictionary[target_ticker].position)
            self.trade(target_ticker, -self.asset_dictionary[target_ticker].position, current_price)

        else: pass
    # more strategy goes here if its beefy
    def process_2(self):
        pass
    # and more strategy code goes here if your strategy is really beefy
    def process_3(self):
        pass

def main():
    TICKER_LIST = ['AAPL']  # define the ticker to trade
    START_STOP_DATES = ('2019-6-15', '2021-6-29')  # define the start and stop dates

    # get the data
    backtest_data = yahooClient.get_close_prices_yahoo(tickers=TICKER_LIST,  # tickers
                                                       start_date=START_STOP_DATES[0],  # start
                                                       stop_date=START_STOP_DATES[1])  # stop
    dummy_strategy = Bollinger()  # define the strategy that will beat the sp500
    engine = alpha.Engine()  # define the engine that will test our epic win strat

    engine.backtest(strategy_object=dummy_strategy,  # tell the engine what strategy we want to backtest
                    backtest_series_dictionary=backtest_data,  # tell the engine what data we want to backtest on
                    starting_cash=25000,  # set the starting cash
                    log=True,
                    filename='Bollinger_Basic_LOG.csv')

if __name__ == '__main__':
    main()

