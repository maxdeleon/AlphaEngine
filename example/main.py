from execution import alpha
from logic import algoManager
from logic.algoManager import Strategy
from market_data import yahooClient
import random

'''
Created by Maximo Xavier DeLeon on 6/23/2021
'''

# create custom trading strategies by declaring a Strategy child class
class dummyBuyStrategy(Strategy):
    def __init__(self):
        Strategy.__init__(self)

    def process_1(self):
        #aapl_close = self.asset_dictionary['AAPL'].close # get the current close price of apple stock
        #msft_close = self.asset_dictionary['MSFT'].close  # get the current close price of microsoft stock
        pass
    # more strategy goes here if its beefy
    def process_2(self):
        pass
    # and more strategy code goes here if your strategy is really beefy
    def process_3(self):
        pass

def main():
    #test_algo_class()
    test_stochastic()

def test_stochastic(): # method to test stochastic processes
    print('testing stochastic process classes...') # tell the user what they just did
    some_asset = {'drift':.2,'volatility':.3,'delta_t':1/255,'initial_price':100} # random parameters
    asset_simulator = alpha.StochasticProcessManager(stochastic_parameters=some_asset) # create a instance of the SPM
    simulations = asset_simulator.build_scenarios(amount=10) # generate 10 different GBM simulations
    for i in simulations:   # print out all of the price lists
        print(i)
        print(simulations[i].head(5))
        print('-=-=-=-=-==--=-=-=-')

if __name__ == '__main__':
    main()