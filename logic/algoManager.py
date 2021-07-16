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
        self.trade_log = pd.DataFrame() # list of dictionaries which will be used to make a dataframe

    # updates the asset by appending the most current bar onto the current bar dataframe
    def update(self,bar):
        self.bars = self.bars.append(bar,ignore_index=False)
        self.returns = np.log(self.bars.Close[-1] / self.bars.Close[-2]) if len(self.bars.index) > 1 else 0 #  calculate returns
        self.trade_log = self.trade_log.append({'date': self.bars.index[-1],
                                                self.ticker + '_current_position': self.position,
                                                self.ticker + '_trade_quantity': 0,
                                                self.ticker + '_trade_price': 0,
                                                self.ticker+'_returns':self.returns},ignore_index=True)

        self.open = self.bars.Open[-1]
        self.high = self.bars.High[-1]
        self.low = self.bars.Low[-1]
        self.close = self.bars.Close[-1]
        self.volume = self.bars.Volume[-1]



    # adjusts the position in the asset object
    def adjust(self,quantity,price):
        self.position += quantity
        self.trade_log = self.trade_log.append({'date':self.bars.index[-1],
                               self.ticker + '_current_position': self.position,
                               self.ticker+'_trade_quantity':quantity,
                               self.ticker+'_trade_price':price,
                               self.ticker+'_returns': self.returns},ignore_index=True)
        self.trade_log = self.trade_log.drop_duplicates(subset=['date'],
                                                        keep='last')

    def get_trades(self):
        export_trade_log = pd.DataFrame(self.trade_log)
        export_trade_log.index = export_trade_log.date
        export_trade_log = export_trade_log.drop('date', axis=1)
        return export_trade_log

# track individual positions --- NOT USED YET ---
class Position:
    def __init__(self,quantity,entry_price):
        self.position_size = quantity
        self.entry_price = entry_price
        self.PnL = 0
    def update(self,quantity,current_price):
        self.position_size = quantity
        self.current_price = current_price
        self.PnL = np.log(self.current_price/self.entry_price)
    def get_value(self):
        return self.position_size*self.current_price

# class to log the cash the strategy has
class Cash:
    def __init__(self):
        self.balance = pd.DataFrame()
    def update(self,date,current_cash):
        self.balance = self.balance.append({'date':date,
                                            'total_cash':current_cash},ignore_index=True)
        # however many times we call this per unique date/time we only care about the end of step cash since the resulting difference will match the cash used to make trades
        self.balance = self.balance.drop_duplicates(subset=['date'],keep='last')

    def get_balances(self):
        export_balance = self.balance.copy()
        export_balance.index = export_balance.date
        export_balance = export_balance.drop('date',axis=1)
        return export_balance

# to be used when optimizer is implemented
class ParameterBook:
    # creates a parameter book object. This class makes a
    # optionally add in patameters to the newly created dictionary
    def __init__(self,parameter_dict=None):
        self.parameters = {} # empty

        if type(parameter_dict) is not None:
            if type(parameter_dict) is dict:
                self.add_parameter(parameter_dict)
            else:
                raise TypeError(parameter_dict,' must be a dictionary')
        else:
            pass

    def add_parameters(self,parameter_dict):
        if type(parameter_dict) is dict:
            for parameter_key in parameter_dict.keys():
                if parameter_key not in self.parameters.keys():
                    self.parameters[parameter_key] = parameter_key[parameter_key]
                else:
                    raise ValueError(parameter_key,' is already a parameter in the parameter book')
        else:
            raise ValueError(parameter_dict,' is not a dictionary')

    def delete_parameters(self,parameter_dict):
        if type(parameter_dict) is dict:
            for parameter_key in parameter_dict.keys():
                if parameter_key in self.parameters.keys():
                    del self.parameters[parameter_key]
                else:
                    raise ValueError(parameter_key, ' is not a parameter in the parameter book')
        else:
            raise ValueError(parameter_dict, ' is not a dictionary')

    def update_parameters(self,parameter_dict):
        if type(parameter_dict) is dict:
            for parameter_key in parameter_dict.keys():
                if parameter_key in self.parameters.keys():
                    self.parameters[parameter_key] = parameter_key[parameter_key]
                else:
                    raise ValueError(parameter_key,' is not a parameter in the parameter book')
        else:
            raise ValueError(parameter_dict,' is not a dictionary')

# order class to manage orders requested by the strategy. works within the order manager class
class Order:
    def __init__(self,ticker, quantity, price,win=0.05,loss=-0.015,message=''):
        self.ticker = ticker
        self.status = 'PENDING' # some useless
        self.data = {'ticker':ticker,'quantity':quantity,'price':price,'fill_price':None,'win_lim':win, 'stop_lim':loss, 'filled':False} # order data
        self.message = message
    def fill(self,fill_price): # this doesnt do anything yet so it will probably be removed at some point
        self.status = 'FILLED'
        self.data['filled'] = True
        self.data['fill_price'] = fill_price

# used to manage the order objects and a layer of complexity to the whole order system
class OrderManager:
    def __init__(self):
        self.pending_orders = {}  # store the order objects

    def create_order(self,ticker, quantity, price,win=0.05,loss=-0.015,message=''):
        # following Jane Street conventions
        # https://www.janestreet.com/static/pdfs/trading-interview.pdf
        if quantity > 0: # buy order
            order_name = str(ticker) +'-$'+ str(round(price,2)) + '-bid-for-' + str(quantity) # create the order name
            self.pending_orders[order_name] = Order(ticker,quantity,price,win,loss,message=message) # create the order and add it to the pending order dict
            return order_name,message # return order name to called
        elif quantity < 0: # sell order
            order_name = str(ticker) +'-'+ str(abs(quantity)) + '-at-$' + str(round(price,2)) # create the order name
            self.pending_orders[order_name] = Order(ticker,quantity,price,win,loss,message=message) # create the order and add it to the pending order dict
            return order_name,message # return order name to called
        elif quantity == 0: # return value error
            raise ValueError('Cannot make order of zero quantity')

    def kill_order(self,order_tag): # if for some reason you need to cancel the order you placed
        if order_tag in self.pending_orders.keys(): # check if the order tag exists in the dictionary keys
            del self.pending_orders[order_tag] # remove the order
        else: raise ValueError('order tag is not recognized') # raise an error saying the tag doesnt exist

    def send_orders(self): # method to return the pending orders to a method in the strategy class
        return self.pending_orders # return the pending orders

    # the send_orders method works with the receive_orders to update the order book

    def receive_orders(self, updated_pending_orders): # method to recieve the previously sent pending orders and check whether or not they were filled
        for order_tag in updated_pending_orders.keys():
            if order_tag in self.pending_orders.keys():
                if updated_pending_orders[order_tag].data['filled']:
                    self.pending_orders[order_tag].data['filled'] = True
                    self.pending_orders[order_tag].data['fill_price'] = updated_pending_orders[order_tag].data['fill_price']
                else: pass
            else: raise ValueError('The recieved order does not appear in the order book please check internal logic')

    def update_book(self): # updates the pending order book
        updated_pending = {}
        for order_tag in self.pending_orders.keys():
            if self.pending_orders[order_tag].data['filled'] == False: # if its not filled then add the order to the new dict
                updated_pending[order_tag] = self.pending_orders[order_tag]
            else: pass # if the order is filled then dont add it to the new dictionary
        self.pending_orders = updated_pending # set the pending order dictionary equal to the updated pending order dictionary

# template class for analysts to use for creating strategies. To create a strategy write your stuff in the process methods after creating a child class of strategy
class Strategy:
    def __init__(self,verbose=True):
        self.verbose = verbose # if true then the strategy class is going to use print statements during actions
        self.asset_dictionary = {} # dictionary that will be used to handle bar data and positions for each asset
        self.CAN_TRADE = False # boolean datatype which controls whether or not the strategy may execute trades. Should be used to catch runtime errors in the algorithms such that nothing bad happens...
        self.set_trade_allocation() # sets the % available cash that can be used to trade
        self.cash_tracker = Cash() # object to track the ammount of available cash
        self.parameter_dictionary = {}
        self.StrategyOrderManager = OrderManager() # creates order manager object
    # used to create asset objects for the asset dictionary. Allows for positions to be tracked alongside price data
    def universe(self,action,ticker):
        if action == 'add' and ticker not in self.asset_dictionary.keys():
            self.asset_dictionary[ticker] = Asset(ticker)
            print('System alert: added',ticker,'to universe')

        elif action == 'remove' and ticker in self.asset_dictionary.keys():
            del self.asset_dictionary[ticker]
            print('System alert: removed', ticker, 'from universe')

    # sets the initial cash
    def set_cash(self,cash):
        self.cash = cash
        self.set_trade_allocation()

    # determine portfolio cash % to be used for market exposure
    def set_trade_allocation(self,allocation=1):
        self.allocation = allocation # method sets a allocation for the cash that can be used to purchase

    # this method sets the cash ammount that is allowed to be used for taking on long positions
    def update_cash_allocation(self):
        self.trade_cash = self.allocation*self.cash
        self.cash_tracker.update(date=self.current_date,
                                current_cash=self.cash)

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
            if self.verbose:
                print('Error',ticker,'not in asset dictionary')
            else: pass

    # tracks trades by altering a trade log dataframe in the asset object
    def trade(self,ticker,quantity,price):
        self.check()
        if self.CAN_TRADE:
            if ticker in self.asset_dictionary.keys():
                if quantity > 0 and quantity*price <= self.trade_cash:
                    self.asset_dictionary[ticker].adjust(quantity,price) # adjust position for long position
                    self.cash += -quantity * price # adjust cash after buying
                    self.update_cash_allocation()
                    return True
                elif quantity < 0 and quantity <= self.asset_dictionary[ticker].position:
                    self.asset_dictionary[ticker].adjust(quantity, price) # adjust position for closing long positions --- SHORTING NOT SUPPORTED
                    self.cash += -quantity*price # adjust cash after selling
                    self.update_cash_allocation()
                    return True
                elif quantity > 0 and quantity*price >= self.trade_cash:
                    if self.verbose:
                        print('System Error | ' + ticker + ' BUY order ' + str(quantity) + 'x$' + str(price) + ' is too large')
                    else:
                        pass
                    return False
            else:
                if self.verbose:
                    print('System Error |',ticker, 'can not be traded!')
                else: pass
                return False
        else:
            if self.verbose:
                print('System Error | algorithm cannot trade!')
            else:
                pass
            return False

    # this is such that the strategy doesnt have a direct interation with the OrderManager and terminal output can be toggled
    def create_order(self,ticker, quantity, price,win=0.05,loss=-0.015,message=''):
        order_name,message = self.StrategyOrderManager.create_order(ticker, quantity, price,win,loss,message)
        if self.verbose:
            print(self.current_date,'| Order notification | CREATED:', order_name,message)
        else: pass


    def handle_orders(self):
        order_dict = self.StrategyOrderManager.send_orders()
        for order_tag in order_dict.keys():
            order_dict[order_tag].data['filled'] = self.trade(ticker=order_dict[order_tag].data['ticker'],
                                              quantity=float(order_dict[order_tag].data['quantity']),
                                              price=float(order_dict[order_tag].data['price']))

            if self.verbose:
                if order_dict[order_tag].data['filled']:
                    print('Order notification | filled:', order_tag)
                else:
                    print('Order notification | unable to fill:', order_tag)
            else: pass

            # future implementation will incorporate the trade limit variables
        self.StrategyOrderManager.receive_orders(order_dict) # receive the orders that were just processed
        self.StrategyOrderManager.update_book() # update the order book to delete any filled orders

    # updates the bars for each asset being tracked
    def update_bars(self,bar_package): # this method recieves a dictionary of bar dataframe slices and appends each ticker's data to its corresponding asset tracking class
        for ticker in bar_package.keys():
            if ticker in self.asset_dictionary.keys():
                self.asset_dictionary[ticker].update(bar_package[ticker])
            else:
                print('error')
        self.current_date = self.asset_dictionary[ticker].bars.index[-1] # get the current date

    # method is what is updated in the engine loop
    def step(self,current_bars):
        self.update_bars(bar_package=current_bars) # update the bars in the asset objects
        self.update_cash_allocation()
        self.process_1() # process the data and also implement strategy logic to refresh every step pt1
        self.process_2()  # process the data and also implement strategy logic to refresh every step pt2
        self.process_3()  # process the data and also implement strategy logic to refresh every step pt3
        self.handle_orders() # handles all the orders so the process methods do not directly interact with the trade method. This is important because I'd like to create a class for handling trades
        # creating a trade class will allow for switching between a broker API and backtest engine easier

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

# 3 different trading strategies
# long term trends
#