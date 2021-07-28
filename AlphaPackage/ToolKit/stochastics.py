import math
import pandas as pd
import numpy as np
from random import random
from scipy import integrate

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

class StochasticProcessManager:
    # manages the stochastic process class
    def __init__(self,stochastic_parameters={'drift':None,'volatility':None,'delta_t':None,'initial_price':None}):
        self.stochastic_parameters = stochastic_parameters # set the base parameters of a simulated asset. OPTIONAL
        self.stochastic_keys =['drift', 'volatility', 'delta_t', 'initial_price']
        # if the stochastic process parameters are left to be none then they must be defined in the generate method

    def generate(self,amount=10,stochastic_parameters=None): # generates a set of multiple stochastic prices
        stochastic_parameters = self.stochastic_parameters if stochastic_parameters is None else stochastic_parameters  # override default parameters if not none type
        if type(stochastic_parameters) is not dict:
            raise TypeError(stochastic_parameters,' must be a dictionary') # check if stochastic_parameters is a dictionary type
        elif list(stochastic_parameters.keys()) != self.stochastic_keys: # check to see if the keys correspond to the accepted list of keys
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
            for process in processes:  # for each process
                time_to_expiration = 1  # set time to expiration as 1
                while ((time_to_expiration - process.dt) > 0):  # iterate through the time to expiration using time step dt
                    process.step()  # generate a price movement
                    time_to_expiration -= process.dt  # update the time to expiration

            return processes  # return a list of StochasticProsses objects that contain price lists of simulated price movements

    def absorb_parameters_from_series(self,df,column='Close'): # this method re writes the stochastic parameters with a user defined series
        sample_size = len(df.index) # get the sample size of the price series
        returns = np.log((df[column]/(df[column].shift(-1))))
        std = np.std(returns) # volatility
        annualized_drift = returns.mean * 252 # annualized drift
        annualized_volatility = std * (252**0.5) # annualized volatility

        self.stochastic_parameters={'drift':annualized_drift,
                               'volatility':annualized_volatility,
                               'delta_t':(1/sample_size),
                               'initial_price':df[column].iloc[0]}

    def build_scenarios(self,amount=10,stochastic_parameters=None,column_name='Close',ticker='GBM'): # builds scenarios and then returns them in the same format as the yahooClient.py method
        alphabet_capitalized = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' # alphabet string capitalized
        random_ticker = ''.join(random.choice(alphabet_capitalized) for letter in range(4))  if ticker is None else ticker# generate a random ticker if one isnt given to the method
        stochastic_tickers = [random_ticker + str(i) for i in range(amount)] # create a list of the tickers with a number ex: [CAT0, CAT1, CAT2 , ... , CATn]
        stochastic_process_list = self.generate(amount=amount, stochastic_parameters=stochastic_parameters) # generate the series
        stochastic_process_df_list = [] # blank list to be filled with the list of nested dictionaries
        for process in stochastic_process_list: # iterate through the list of processes
            stochastic_process_df_list.append(pd.DataFrame(data=process.prices,index=list(np.arange(len(process.prices))),columns= [column_name])) # append casted stochastic data to a df
        scenarios = dict(zip(stochastic_tickers,stochastic_process_df_list)) # build a dictionary of nested pandas dataframes to be used with the backtester
        return scenarios # return the scenario dictionary


class StochSignal:
    def __init__(self, parameter_dict=None):
        self.parameters = {'drift': 0, 'volatility': 0} if parameter_dict is None else parameter_dict

    def set_parameters(self, parameter_dict):
        self.parameters = parameter_dict

    def compute_bound(self, s0, pi, mu, sigma, t):
        return np.log(pi / (s0 * np.exp((mu - 0.5 * (sigma ** 2)) * t))) / (sigma * np.sqrt(t))

    # computes the probability of being above or under a specified price
    def compute_probability(self, s0, pi, mu, sigma, t, condition='over'):
        psi = lambda x: ((2 * np.pi) ** -0.5) * np.exp(-0.5 * (x ** 2))

        if condition == 'over':
            lower_bound = self.compute_bound(s0, pi, mu, sigma, t)
            result = integrate.quad(psi, lower_bound, np.inf)
        elif condition == 'under':
            upper_bound = self.compute_bound(s0, pi, mu, sigma, t)
            result = integrate.quad(psi, -np.inf, upper_bound)
        else:
            return 'error'
        return result[0], result[-1]