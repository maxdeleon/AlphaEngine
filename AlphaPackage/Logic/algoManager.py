from AlphaPackage.Logic.management import *
'''
Created by Maximo Xavier DeLeon on 6/23/2021
'''


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
        self.trade_count = 0
    # used to create asset objects for the asset dictionary. Allows for positions to be tracked alongside price data
    def universe(self,action,ticker):
        if action == 'add' and ticker not in self.asset_dictionary.keys():
            self.asset_dictionary[ticker] = Asset(ticker)
            if self.verbose:
                print('System alert: added',ticker,'to universe')
            else: pass

        elif action == 'remove' and ticker in self.asset_dictionary.keys():
            del self.asset_dictionary[ticker]
            if self.verbose:
                print('System alert: removed', ticker, 'from universe')
            else: pass
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
        return {'can_trade':self.CAN_TRADE,'cash_balance':self.cash_tracker.get_balances[-1],'total_trades':self.trade_count}

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
                    print(self.current_date,'| Order notification | GOOD FILL:', order_tag)
                    self.trade_count +=1
                else:
                    print(self.current_date,'| Order notification | FILL FAIL:', order_tag)
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
        self.process_1() # process the data and also implement strategy Logic to refresh every step pt1
        self.process_2()  # process the data and also implement strategy Logic to refresh every step pt2
        self.process_3()  # process the data and also implement strategy Logic to refresh every step pt3
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