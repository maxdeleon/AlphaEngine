import pandas as pd
from AlphaPackage.ToolKit import StochasticProcessManager
import copy
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

        if strategy_object.verbose == True:
            print('Running Simulation',end=' ')  # tell the unsuspecting user that they initiated a backtest and its beginning right now
        else: pass

        # main back test loop
        for row_index in range(min(backtest_data_lengths)):
            current_bar_package = {} # empty dictionary
            for ticker in backtest_series_dictionary.keys(): # for each of assets we are tracking
                data = backtest_series_dictionary[ticker] # access the nested dataframe within the dicitonary
                current_bar = data.iloc[row_index] # get the current bar of the backtest iteration
                current_bar_package[ticker] = current_bar # add that current bar for the current ticker into our "bar package"

            strategy_object.step(current_bar_package)  # give the bar package to the strategy to be parsed and dealt with properly

        if strategy_object.verbose == True:
            print('=> Simulation Complete!') # tell the user their strategy is done being slammed by the backtest
        else: pass

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

    def evaluate(self,eval_params,return_csv=False,filename='default_evaluation_data.csv'):
        scenario_dict = {}
        if 'asset_dict_parameters' in eval_params.keys():
            scenario_params = eval_params['asset_dict_parameters'] # said parameters
            scenario_generator = StochasticProcessManager() # create an instance of our SPM class
            for ticker in scenario_params.keys(): # iterate through the parameters to create simulated asset price movements
                # generate a dictionary of scenarios and append it to the scenario dict
                scenario_dict[ticker+'_GBM'] = scenario_generator.build_scenarios(amount=eval_params['sample_size'],stochastic_parameters=scenario_params[ticker],column_name='Close',ticker=ticker)

            trial_dict = {}
            for i in range(1,eval_params['sample_size']):
                current_trial_dict = {}
                # this section iterates through the dictionaries of simulated asset price movements to build trials for testing strategy/benchmark
                for ticker in scenario_params.keys():
                    current_trial_dict[ticker] = scenario_dict[ticker+'_GBM'][list(scenario_dict[ticker+'_GBM'].keys())[-1]]
                    # this section may get pruned out
                    current_trial_dict[ticker]['Open'] = 0
                    current_trial_dict[ticker]['High'] = 0
                    current_trial_dict[ticker]['Low'] = 0
                    current_trial_dict[ticker]['Volume'] = 0
                    del scenario_dict[ticker+'_GBM'][list(scenario_dict[ticker+'_GBM'].keys())[-1]]

                    trial_dict['trial_'+str(i)] = current_trial_dict

            # dict to hold our simulated results
            pnl_dict = {'strategy_pnl':{},'benchmark_pnl': {}}

            # iterate through the number of trials and test the strategy N times
            for i in range(1,eval_params['sample_size']):
                # copy the Strategy objects for the current iteration of backtests
                strategy_instance = copy.deepcopy(eval_params['strategy'])
                benchmark_instance = copy.deepcopy(eval_params['benchmark'])
                # set the Strategy objects to not make any chatter
                strategy_instance.verbose = False
                benchmark_instance.verbose = False
                # run the strategy backtest
                pnl_dict['strategy_pnl']['trial_'+str(i)] = self.backtest(strategy_object=strategy_instance,
                                                                            backtest_series_dictionary=trial_dict['trial_'+str(i)],
                                                                            starting_cash=eval_params['starting_cash'],
                                                                            log=False)
                # run the benchmark backtest
                pnl_dict['benchmark_pnl']['trial_'+str(i)] = self.backtest(strategy_object=benchmark_instance,
                                                                             backtest_series_dictionary=trial_dict['trial_'+str(i)],
                                                                             starting_cash=eval_params['starting_cash'],
                                                                             log=False)
            # once all that testing is done
            # create a dataframe that has the data from our GBM tests
            returns_df = pd.DataFrame()
            returns_df['strategy_pnl'] = pnl_dict['strategy_pnl'].values() # strategy pnl data
            returns_df['benchmark_pnl'] = pnl_dict['strategy_pnl'].values() # benchmark pnl data
            returns_df.index = pnl_dict['strategy_pnl'].keys() # set the index of the data frame


            # calculate mean return
            strategy_mean_returns = returns_df['strategy_pnl'].mean()
            benchamrk_mean_returns = returns_df['benchmark_pnl'].mean()

            # calculate uncertainty in the mean
            strategy_uncertainty_in_the_mean = strategy_mean_returns*(returns_df['strategy_pnl'].std()/len(returns_df.index))
            benchamrk_uncertainty_in_the_mean = strategy_mean_returns*(returns_df['benchmark_pnl'].std()/len(returns_df.index))

            # calculate the t-statistic, if someone else can please review this I would appreciate it.
            t_statistic = (strategy_mean_returns-benchamrk_mean_returns)/(((strategy_uncertainty_in_the_mean)**2 + (benchamrk_uncertainty_in_the_mean)**2)**.05)

            print('Mean Strategy PnL:',strategy_mean_returns, '|','Mean Benchmark PnL:',benchamrk_mean_returns)

            print('t-statistic:', t_statistic,end=' => ') # print out the t_statistic for the user to see

            # make the data driven decision on whether or not the strategy's performance is distinguishable from the benchmark
            if abs(t_statistic) <= 1:
                print('Strategy and benchmark are indistinguishable given their uncertainties. Cannot conclude that strategy and benchmark are different.')
                signifigance_sign = -1
            elif 1 <= abs(t_statistic) <= 3:
                print('Strategy and benchmark are in tension -- they may be distinguishable, but the evidence is tenuous. Consider increasing sample size.')
                signifigance_sign = 0
            elif abs(t_statistic) >= 3:
                print('Strategy and benchmark are distinguishable given their uncertainties. In other words, we can conclude that strategy and benchmark are very likely to be different.')
                signifigance_sign = 1
            else:
                print('error? how did you get here') # this should'nt be seen by whoever is running this method
                signifigance_sign = 2


            ''' 
            H_0: A and B are not the same
            H_1: A and B are the same
            
            - if strategy pnl is greater and distinguishable from benchmark then the strategy is good for given market conditions
            - if strategy pnl is greater and is not distinguishable from benchmark then the strategy should be evaluated further
            
            - if strategy pnl is less and distinguishable from benchmark then the strategy is not so goog for given market conditions
            - if strategy pnl is less and is not distinguishable from benchmark then the strategy should be evaluated further
            
            
            --This was taken from PHYS 2305-2306 lab statistics handbook and will be used as a reference for the time being --
            For |t′|≤1:
            This result does not mean that A and B are the same. This result only tells us that we cannot distinguish A and B using the available data.
            For example, suppose you improve your experimental design, perform new, better measurements, and reduce the statistical uncertainties in A and B. After applying the t'-test to this new data, you might discover that A and B are now distinguishable.
            In summary, when you perform a t'-test and obtain|𝑡′|≤1, you should consider improving your measurements to decrease the statistical uncertainties in A and B. Poor precision (i.e., overinflated uncertainties) may be hiding a subtle difference between your two measured values.
            
            1< |t′|<3:
            This result means that A and B are in tension, and you should endeavor to obtain more conclusive evidence. As such, you should improve your measurements to decrease the statistical uncertainties in A and B.
            
            |t′|≥3:
            This result means that we can distinguish A and B using the available data. If your model predicts that A and B should be indistinguishable, then this result implies that you need to re-evaluate your model and possibly revise it.

            '''


            if return_csv:
                returns_df.to_csv(filename)
            else:
                pass

            return (t_statistic,signifigance_sign,returns_df) # return the important information as a tuple









        # +++++++++++++++++ do this now +++++++++++++++++
        # take in the strategy, a benchmark, GBM parameters, N number of GBM processes for M assets
        # run strategy on each GBM process along side the benchmark
        # t-test for signifigance, return p-value



        # +++++++++++++++++ do this later +++++++++++++++++
        # run strategy and benchmark on actual historical data with similar if not identical GBM parameters
        # determine whether or not the strategy just got lucky or is within the convidence interval produced from our GBM