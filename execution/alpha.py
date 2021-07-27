import pandas as pd
import math, random
import numpy as np
from tools.Stochastics import StochasticProcessManager
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

        print('Running Simulation',end=' ') if strategy_object.verbose == False else print('Running Simulation') # tell the unsuspecting user that they initiated a backtest and its beginning right now

        # main back test loop
        for row_index in range(min(backtest_data_lengths)):
            current_bar_package = {} # empty dictionary
            for ticker in backtest_series_dictionary.keys(): # for each of assets we are tracking
                data = backtest_series_dictionary[ticker] # access the nested dataframe within the dicitonary
                current_bar = data.iloc[row_index] # get the current bar of the backtest iteration
                current_bar_package[ticker] = current_bar # add that current bar for the current ticker into our "bar package"

            strategy_object.step(current_bar_package)  # give the bar package to the strategy to be parsed and dealt with properly


        print('=> Simulation Complete!') # tell the user their strategy is done being slammed by the backtest


        return self.build_log(strategy_object=strategy_object,filename=filename,make_csv=log)


    def build_log(self,strategy_object,filename='BACKTEST_LOG.csv',make_csv=False):

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


        #print('PnL: $' + str(log_df.strategy_value.iloc[-1]-log_df.strategy_value.iloc[0]) + '| PnL % '+ str(100*(log_df.strategy_value.iloc[-1]-log_df.strategy_value.iloc[0])/log_df.strategy_value.iloc[0])) # print out PnL to the terminal
        pnl_percent = 100*((log_df.strategy_value.iloc[-1]-log_df.strategy_value.iloc[0])/log_df.strategy_value.iloc[0])
        #print('Exporting trade data to',filename)

        if make_csv:
            log_df.to_csv(filename)
        else: pass

        return pnl_percent

    '''
    eval_params = {'strategy':None,
                   'benchmark':None,
                   'starting_cash':float,
                   'asset_dict_parameters':{'ticker':{'drift':None,'volatility':None,'delta_t':None,'initial_price':None}},
                   'sample_size':100}
    '''

    def evaluate(self,eval_params):

        scenario_dict = {}
        if 'asset_dict_parameters' in eval_params.keys():
            scenario_params = eval_params['asset_dict_parameters']
            scenario_generator = StochasticProcessManager()
            for ticker in scenario_params.keys():
                # generate a dictionary of scenarios and append it to the scenario dict
                scenario_dict[ticker+'_GBM'] = scenario_generator.build_scenarios(amount=eval_params['sample_size'],stochastic_parameters=scenario_params[ticker],column_name='Close',ticker=ticker)

            trial_dict = {}
            for i in range(1,eval_params['sample_size']):
                current_trial_dict = {}
                for ticker in scenario_params.keys():
                    current_trial_dict[ticker] = scenario_dict[ticker+'_GBM'][list(scenario_dict[ticker+'_GBM'].keys())[-1]]
                    current_trial_dict[ticker]['Open'] = 0
                    current_trial_dict[ticker]['High'] = 0
                    current_trial_dict[ticker]['Low'] = 0
                    current_trial_dict[ticker]['Volume'] = 0
                    del scenario_dict[ticker+'_GBM'][list(scenario_dict[ticker+'_GBM'].keys())[-1]]

                    trial_dict['trial_'+str(i)] = current_trial_dict


            # do the backtesting now
            strategy_list = [eval_params['strategy'] for n in range(eval_params['sample_size'])]
            benchmark_list = [eval_params['benchmark'] for n in range(eval_params['sample_size'])]
            pnl_dict = {'strategy_pnl':{},
                        'benchmark_pnl': {}}

            for i in range(1,eval_params['sample_size']):
                pnl_dict['strategy_pnl']['trial_'+str(i)] = self.backtest(strategy_object=strategy_list[i],
                                                                            backtest_series_dictionary=trial_dict['trial_'+str(i)],
                                                                            starting_cash=eval_params['starting_cash'],
                                                                            log=False)
                ''' 
                pnl_dict['benchmark_pnl']['trial_'+str(i)] = self.backtest(strategy_object=benchmark_list[i],
                                                                             backtest_series_dictionary=trial_dict['trial_'+str(i)],
                                                                             starting_cash=eval_params['starting_cash'],
                                                                             log=False)
                '''

                #print('strategy:',pnl_dict['strategy_pnl']['trial_'+str(i)], ' benchmark:',pnl_dict['strategy_pnl']['trial_'+str(i)])






        # +++++++++++++++++ do this now +++++++++++++++++
        # take in the strategy, a benchmark, GBM parameters, N number of GBM processes for M assets
        # run strategy on each GBM process along side the benchmark
        # t-test for signifigance, return p-value



        # +++++++++++++++++ do this later +++++++++++++++++
        # run strategy and benchmark on actual historical data with similar if not identical GBM parameters
        # determine whether or not the strategy just got lucky or is within the convidence interval produced from our GBM

