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
        self.returns = np.log(self.bars.Close.iloc[-1] / self.bars.Close.iloc[-2]) if len(self.bars) > 1 else 0 #  calculate returns



        self.trade_log = self.trade_log.append({'date': self.bars.index[-1],
                                                self.ticker + '_current_position': self.position,
                                                self.ticker + '_trade_quantity': 0,
                                                self.ticker + '_trade_price': 0,
                                                self.ticker+'_returns':self.returns},ignore_index=True)

        self.open = self.bars.Open.iloc[-1] if 'Open' in self.bars.columns else 0
        self.high = self.bars.High.iloc[-1] if 'High' in self.bars.columns else 0
        self.low = self.bars.Low.iloc[-1] if 'Low' in self.bars.columns else 0
        self.close = self.bars.Close.iloc[-1] if 'Close' in self.bars.columns else 0
        self.volume = self.bars.Volume.iloc[-1] if 'Volume' in self.bars.columns else 0



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
            else: raise ValueError('The recieved order does not appear in the order book please check internal Logic')

    def update_book(self): # updates the pending order book
        updated_pending = {}
        for order_tag in self.pending_orders.keys():
            if self.pending_orders[order_tag].data['filled'] == False: # if its not filled then add the order to the new dict
                updated_pending[order_tag] = self.pending_orders[order_tag]
            else: pass # if the order is filled then dont add it to the new dictionary
        self.pending_orders = updated_pending # set the pending order dictionary equal to the updated pending order dictionary