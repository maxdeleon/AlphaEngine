import pandas as pd
'''
Created by Maximo Xavier DeLeon on 6/23/2021
'''
class Engine:
    def __init__(self):
        pass

    def backtest(self,strategy,data_dict,starting_cash=100000,log=False,filename='BACKTEST_LOG.csv'):
        '''
        :param strategy:
        :param data:
        :param starting_cash:
        :return:
        '''

        strategy.set_cash(starting_cash) # set the starting cash

        # iterate through the dictionary keys and use those to define the universe of stocks our strategy will pay attention to
        for ticker in data_dict.keys():
            strategy.universe(action='add',ticker=ticker) # call the method from strategy


        backtest_data_lengths = [len(data_dict[ticker].index) for ticker in data_dict.keys()] # find the shortest backtest data - this is to stop errors for series with different lengths

        print('Running Simulation') # tell the unsuspecting user that they initiated a backtest and its beginning right now

        # main back test loop
        for row_index in range(min(backtest_data_lengths)):
            current_bar_package = {} # empty dictionary
            for ticker in data_dict.keys(): # for each of assets we are tracking
                data = data_dict[ticker] # access the nested dataframe within the dicitonary
                current_bar = data.iloc[row_index] # get the current bar of the backtest iteration
                current_bar_package[ticker] = current_bar # add that current bar for the current ticker into our "bar package"

            strategy.step(current_bar_package)  # give the bar package to the strategy to be parsed and dealt with properly


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


        print('PnL: $' + str(log_df.strategy_value.iloc[-1]-log_df.strategy_value.iloc[0]))

        print('Exporting trade data to',filename)
        log_df.to_csv(filename)