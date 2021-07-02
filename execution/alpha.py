import pandas as pd
import math, random
import numpy as np
'''
Created by Maximo Xavier DeLeon on 6/23/2021
'''
class Engine:
    def __init__(self):
        pass

    def backtest(self, strategy_object, backtest_series_dictionary, starting_cash=100000, log=False, filename='BACKTEST_LOG.csv'):
        '''
        :param strategy_object:
        :param backtest_series_dictionary:
        :param starting_cash:
        :return:
        '''

        strategy_object.set_cash(starting_cash) # set the starting cash

        # iterate through the dictionary keys and use those to define the universe of stocks our strategy will pay attention to
        for ticker in backtest_series_dictionary.keys():
            strategy_object.universe(action='add', ticker=ticker) # call the method from strategy


        backtest_data_lengths = [len(backtest_series_dictionary[ticker].index) for ticker in backtest_series_dictionary.keys()] # find the shortest backtest data - this is to stop errors for series with different lengths

        print('Running Simulation') # tell the unsuspecting user that they initiated a backtest and its beginning right now

        # main back test loop
        for row_index in range(min(backtest_data_lengths)):
            current_bar_package = {} # empty dictionary
            for ticker in backtest_series_dictionary.keys(): # for each of assets we are tracking
                data = backtest_series_dictionary[ticker] # access the nested dataframe within the dicitonary
                current_bar = data.iloc[row_index] # get the current bar of the backtest iteration
                current_bar_package[ticker] = current_bar # add that current bar for the current ticker into our "bar package"

            strategy_object.step(current_bar_package)  # give the bar package to the strategy to be parsed and dealt with properly


        print('Simulation Complete!') # tell the user their strategy is done being slammed by the backtest

        if log:
            self.build_log(strategy_object=strategy,filename=filename)

    def build_log(self,strategy_object,filename='BACKTEST_LOG.csv'):

        log_df = strategy_object.cash_tracker.get_balances() # get the cash balances of the strategy
        log_df['strategy_value'] = log_df['total_cash'] # create a column to track the value of the strategy's holdings
        df_lens = [len(log_df.index)] # debug tool

        for ticker in strategy_object.asset_dictionary.keys(): # iterate through the tickers
            current_asset_closes = pd.DataFrame((strategy_object.asset_dictionary[ticker].bars.Close).rename(ticker+'_close')) # ticker close values
            df_lens.append(len(current_asset_closes.index)) # debug
            log_df = pd.concat([log_df, current_asset_closes.set_index(log_df.index[-len(current_asset_closes):])],axis=1) # add the close to the main tracking df

        for ticker in strategy_object.asset_dictionary.keys():  # iterate through the tickers
            current_asset_log_df = strategy_object.asset_dictionary[ticker].get_trades() # get the asset data
            df_lens.append(len(current_asset_log_df.index)) # debug
            log_df = pd.concat([log_df,current_asset_log_df.set_index(log_df.index[-len(current_asset_log_df):])],axis=1) # add the positions and trade data to the main tracking df
            log_df['strategy_value'] += log_df[ticker+'_close'] * log_df[ticker+'_current_position'] # calculate the value of the holdings


        print('PnL: $' + str(log_df.strategy_value.iloc[-1]-log_df.strategy_value.iloc[0])) # print out PnL to the terminal

        print('Exporting trade data to',filename)
        log_df.to_csv(filename)



# This section is to simulate market prices given drift,volatility,delta_t,initial_price as parameters
# Ideally this will allow for us to tests shorter term entry and exit points for given assets without worrying about over fitting on historical prices
class StochasticProcess:
    # create stochastic processes for simulating price movements
    def __init__(self,drift,volatility,delta_t,initial_price):
        self.mu = drift # drift direction of movement
        self.sigma = volatility # volatility of an asset
        self.dt = delta_t # time step ex; 1/255 to generate 255 steps of close prices
        self.current_price = initial_price # set the inital price of the asset as the current when creating the class
        self.prices = [initial_price] # have a list of close prices headed by the initial price

    # step through the stochastic process
    def step(self):
        '''
        dS / S = mu * dt + sigma * dW
        dS = (mu * dt + sigma * dW) * S
        Price change = (drift * change_in_time + volatility  * change_in_brownian_motion) * current_asset_price
        '''
        dW = np.random.normal(0, math.sqrt(self.dt)) # generate a change in brownian motion from a normal distribution
        dS = (self.mu * self.dt + self.sigma*dW)*self.current_price # calculate the change in price given GBM parameters and dW
        self.current_price = self.current_price + dS # set the new asset price to the previous price + the price change
        self.prices.append(self.current_price) # append the prices to the price list

class ProcessManager:
    # manages the stochastic process class
    def __init__(self,stochastic_parameters={'drift':None,'volatility':None,'delta_t':None,'initial_price':None}):
        self.stochastic_parameters = stochastic_parameters # set the base parameters of a simulated asset. OPTIONAL
        self.stochastic_keys =['drift', 'volatility', 'delta_t', 'initial_price']
        # if the stochastic process parameters are left to be none then they must be defined in the generate method

    def generate(self,amount=10,stochastic_parameters=None): # generates a set of multiple stochastic prices
        stochastic_parameters = self.stochastic_parameters if stochastic_parameters is None else stochastic_parameters  # override default parameters if not none type
        if type(stochastic_parameters) is not dict:
            raise TypeError(stochastic_parameters,' must be a dictionary') # check if stochastic_parameters is a dictionary type
        elif stochastic_parameters.keys() != self.stochastic_keys: # check to see if the keys correspond to the accepted list of keys
            raise IndexError ('parameter keys do not coincide to', self.stochastic_keys)
        elif not all(stochastic_parameters.values()): # make sure there are no none types in the dictionary values
            raise  TypeError('stochtastic process parameters contain None type')
        elif not all(type(value) is float or int for value in stochastic_parameters.values()): # make sure all the values are numeric
            raise TypeError('stochtastic process parameters contain non numeric type')
        else: # if everything works out then create multiple stochastic simulations
            processes = []
            for i in range(0,amount): # create user defined set of stochastic process
                processes.append(StochasticProcess(drift=stochastic_parameters['drift'],
                                                   volatility=stochastic_parameters['volatility'],
                                                   delta_t=stochastic_parameters['delta_t'],
                                                   initial_price=stochastic_parameters['initial_price']))
                for process in processes: # for each process
                    time_to_expiration = 1 # set time to expiration as 1
                    while((time_to_expiration - process.dt) > 0 ): # iterate through the time to expiration using time step dt
                        process.step() # generate a price movement
                        time_to_expiration -= process.dt # update the time to expiration

                return processes # return a list of StochasticProsses objects that contain price lists of simulated price movements
