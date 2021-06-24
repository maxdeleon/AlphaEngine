import numpy as np
import pandas as pd

'''
Created by Maximo Xavier DeLeon on 6/23/2021
'''

class Asset:
    def __init__(self,ticker):
        self.ticker = ticker # ticker of stock or crypto
        self.bars = pd.DataFrame() # dataframe to store bar data
        self.position = 0 # default positon size
        self.trade_log = [] # list of dictionaries which will be used to make a dataframe

    # updates the asset by appending the most current bar onto the current bar dataframe
    def update(self,bar):
        self.bars = self.bars.append(bar,ignore_index=False)
        self.open = self.bars.Open[-1]
        self.high = self.bars.High[-1]
        self.low = self.bars.Low[-1]
        self.close = self.bars.Close[-1]
        self.volume = self.bars.Volume[-1]

    # adjusts the position in the asset object
    def adjust(self,quantity,price):
        self.position += quantity
        self.trade_log.append({'date':self.bars.index[-1],
                               'trade_quantity':quantity,
                               'trade_price':price})
    def get_trades(self):
        return pd.DataFrame(self.trade_log)

# template class for analysts to use for creating strategies. To create a strategy write your stuff in the process methods after creating a child class of strategy
class Strategy:
    def __init__(self):
        self.asset_dictionary = {} # dictionary that will be used to handle bar data and positions for each asset
        self.CAN_TRADE = False # boolean datatype which controls whether or not the strategy may execute trades. Should be used to catch runtime errors in the algorithms such that nothing bad happens...
        self.set_trade_allocation()
    # used to create asset objects for the asset dictionary. Allows for positions to be tracked alongside price data
    def universe(self,action,ticker):
        if action == 'add' and ticker not in self.asset_dictionary.keys():
            self.asset_dictionary[ticker] = Asset(ticker)
            print('System alert: added',ticker,'to universe')

        elif action == 'remove' and ticker in self.asset_dictionary.keys():
            del self.asset_dictionary[ticker]
            print('System alert: removed', ticker, 'from universe')

    # sets the cash that is available
    def set_cash(self,cash):
        self.cash = cash
        self.set_trade_allocation()

    # determine portfolio cash % to be used for market exposure
    def set_trade_allocation(self,allocation=1):
        self.allocation = allocation # method sets a allocation for the cash that can be used to purchase

    # this method sets the cash ammount that is allowed to be used for taking on long positions
    def update_cash_allocation(self):
        self.trade_cash = self.allocation*self.cash

    # checks whether or not the algorithm is allowed to trade given the available cash and size of the asset tracking dictionary
    def check(self):
        if len(self.asset_dictionary.keys()) > 0 and self.cash > 0:
            self.CAN_TRADE = True
        else:
            self.CAN_TRADE = False

    # returns algorithm status alongside an overview of the performance at a given instant in time
    def status(self):
        pass

    # returns a folder containing overall strategy performance alongside trade logs
    def report(self):
        pass

    def return_trade_logs(self,ticker=None):
        if ticker is None:
            trade_data = {}
            for ticker in self.asset_dictionary.keys():
                trade_data[ticker] = self.asset_dictionary[ticker].get_trades()

            return trade_data
        elif type(ticker) is str and ticker in self.asset_dictionary.keys():
            trade_data = {ticker:self.asset_dictionary[ticker].get_trades()}
            return trade_data
        else:
            print('Error',ticker,'not in asset dictionary')

    # tracks trades by altering a trade log dataframe in the asset object
    def trade(self,ticker,quantity,price):
        if self.CAN_TRADE:
            if ticker in self.asset_dictionary.keys():
                if quantity > 0 and quantity*price <= self.trade_cash:
                    self.asset_dictionary[ticker].adjust(quantity,price) # adjust position for long position
                    self.cash += -quantity * price # adjust cash after buying
                elif quantity < 0 and quantity <= self.asset_dictionary[ticker].position:
                    self.asset_dictionary[ticker].adjust(quantity, price) # adjust position for closing long positions --- SHORTING NOT SUPPORTED
                    self.cash += -quantity*price # adjust cash after selling
                else:
                    print('error')
            else:
                print('Error:',ticker, 'can not be traded!')
        else:
            print('Error: algorithm cannot trade!')

    # updates the bars for each asset being tracked
    def update_bars(self,bar_package): # this method recieves a dictionary of bar dataframe slices and appends each ticker's data to its corresponding asset tracking class
        for ticker in bar_package.keys():
            if ticker in self.asset_dictionary.keys():
                self.asset_dictionary[ticker].update(bar_package[ticker])
            else:
                print('error')

    # method is what is updated in the engine loop
    def step(self,current_bars):
        self.update_cash_allocation()
        self.update_bars(bar_package=current_bars) # update the bars in the asset objects
        self.update_cash_allocation()
        self.process_1() # process the data and also implement strategy logic to refresh every step pt1
        self.update_cash_allocation()
        self.process_2()  # process the data and also implement strategy logic to refresh every step pt2
        self.update_cash_allocation()
        self.process_3()  # process the data and also implement strategy logic to refresh every step pt3

    # strategy goes here
    def process_1(self):
        pass

    # more strategy goes here if its beefy
    def process_2(self):
        pass

    # more strategy goes here if its really beefy
    def process_3(self):
        pass

# easter egg... jk just testing git - max