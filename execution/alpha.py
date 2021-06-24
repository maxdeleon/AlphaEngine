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
            trade_logs = strategy.return_trade_logs() # pull the trade logs
            for ticker in trade_logs.keys(): # for each asset in the universe print a summary of the trade logs
                print(ticker, 'trade log')
                print(trade_logs[ticker])

            print(strategy.cash_wallet.balance)
