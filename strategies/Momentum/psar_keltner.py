from logic.algoManager import Strategy
from strategies.benchmark.benchmark import BuyAndHold
import math
import numpy as np
from scipy import integrate
import pandas as pd
from market_data import yahooClient
from execution import alpha
from talib import MACD


class KeltnerChannelStrategy(Strategy):
    def __init__(self):
        Strategy.__init__(self)
        self.verbose = False #
        self.in_market = False # by default the algo will begin with no positions and thus is not in the market
        self.trade_limits = (0.1,0.03) # set the trade limits

    def get_kc(self,high, low, close, kc_lookback, multiplier, atr_lookback):
        tr1 = pd.DataFrame(high - low)
        tr2 = pd.DataFrame(abs(high - close.shift()))
        tr3 = pd.DataFrame(abs(low - close.shift()))
        frames = [tr1, tr2, tr3]
        tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
        atr = tr.ewm(alpha=1 / atr_lookback).mean()

        kc_middle = close.ewm(kc_lookback).mean()
        kc_upper = close.ewm(kc_lookback).mean() + multiplier * atr
        kc_lower = close.ewm(kc_lookback).mean() - multiplier * atr

        return kc_middle, kc_upper, kc_lower

    def process_1(self):
        self.cash_allocation = {}  # cash allocation dictionary
        # cash to be used at any time for each asset
        for ticker in self.asset_dictionary.keys():  # iterate through the tickers in the asset universe
            self.cash_allocation[ticker] = self.trade_cash / len(self.asset_dictionary.keys())  # assign each asset an even cash allocation for trading

    def process_2(self):
        self.set_trade_allocation(0.7) # max cash to be used at any time for any asset

        for ticker in self.asset_dictionary.keys():
            high = self.asset_dictionary[ticker].bars.High
            low = self.asset_dictionary[ticker].bars.Low
            close = self.asset_dictionary[ticker].bars.Close
            self.asset_dictionary[ticker].bars['kc_middle'], self.asset_dictionary[ticker].bars['kc_upper'],self.asset_dictionary[ticker].bars['kc_lower'] = self.get_kc(high,low,close,20, 2, 10)


            if close[-1] <= self.asset_dictionary[ticker].bars['kc_lower'][-1]:
                #trade_size = math.floor(self.cash_allocation[ticker]/close[-1])
                self.create_order(ticker,10,close[-1],message='keltner channel buy signal')

            elif close[-1] >= self.asset_dictionary[ticker].bars['kc_middle'][-1] and close[-1] >= self.asset_dictionary[ticker].bars['kc_upper'][-1] and self.asset_dictionary[ticker].position > 0:
                self.create_order(ticker, -self.asset_dictionary[ticker].position, close[-1], message='keltner channel sell signal')



def main():
    COINS_TICKERS = ['USO','BNO','UGA','UNG','CORN','COW','SOYB','WEAT','JO','SGG','BAL','IAU','SLV','CPER']

    START_STOP_DATES = ('2020-7-15', '2021-7-19')  # define the start and stop dates

    for ticker in COINS_TICKERS:
        # get the data
        backtest_data = yahooClient.get_close_prices_yahoo(tickers=[ticker],  # tickers
                                                           start_date=START_STOP_DATES[0],  # start
                                                           stop_date=START_STOP_DATES[1])  # stop


        kc_strategy = KeltnerChannelStrategy()  # define the strategy that will beat the sp500
        benchmark = BuyAndHold(allocation_dict={ticker:1})
        engine = alpha.Engine()  # define the engine that will test our epic win strat


        strategy_cumulative_returns = engine.backtest(strategy_object=kc_strategy,  # tell the engine what strategy we want to backtest
                                                      backtest_series_dictionary=backtest_data,  # tell the engine what data we want to backtest on
                                                      starting_cash=25000,  # set the starting cash
                                                      log=False,
                                                      filename='KeltnerChannelStrategy_version1_LOG.csv')

        benchmark_cumulative_returns = engine.backtest(strategy_object=benchmark,# tell the engine what strategy we want to backtest
                                                      backtest_series_dictionary=backtest_data,# tell the engine what data we want to backtest on
                                                      starting_cash=25000, # set the starting cash
                                                      log=False,
                                                      filename='benchmark.csv')

        strategy_relative_return = strategy_cumulative_returns - benchmark_cumulative_returns

        print('Strategy Absolute % :',strategy_cumulative_returns ,'| Relative Returns to benchmark % :',strategy_relative_return)




if __name__ == '__main__':
    main()

