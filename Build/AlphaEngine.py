from AlphaPackage.Execution import alpha
from AlphaPackage.MarketData import yahooClient
from datetime import datetime
import sys
import os.path
import pickle


class RunBacktest():
    def __init__(self):
        self.description = 'runs a backtest given a specific strategy file and a data parameter file'
        self.command_names = ('-b', '-backtest')

        self.arguments = {'arg_2':('default_strategy.py'),
                          'arg_3':('backtest_params.txt')}
    def perform(self):
        HALT = False
        strategy_pickle_path = self.arguments['arg_2']
        backtest_parameter_path = self.arguments['arg_3']
        if os.path.isfile(strategy_pickle_path) and os.path.isfile(backtest_parameter_path):

            parameter_file = open(backtest_parameter_path, 'r')
            print('Reading Parameter File', parameter_file)
            lines = parameter_file.readlines()
            backtest_parameters = {}
            for line in lines:
                if line[0] == '~':
                    line = line.strip('\n')
                    line = line.strip('~')
                    line = line.split('=')
                    backtest_parameters[line[0]] = line[1]
                else: pass

            # datetime object containing current date and time

            if 'data_source' in backtest_parameters.keys():
                if backtest_parameters['data_source'] == 'pickle':
                    # do stuff to unpack the data
                    # if the backtest data is in a pickle
                    if 'pickle_path' in backtest_parameters.keys() and os.path.isfile(backtest_parameters['pickle_path']):
                        backtest_data = pickle.load(open(backtest_parameters['pickle_path'],'rb'))
                    else: HALT = True


                        # if the backtest data is being fetched from yahoofinance
                elif backtest_parameters['data_source'] == 'yahoo':
                    if 'asset_universe' in backtest_parameters.keys() and 'start_date' in backtest_parameters.keys() and 'stop_date' in backtest_parameters.keys():
                        ticker_list = list(backtest_parameters['asset_universe'])
                        backtest_data = yahooClient.get_close_prices_yahoo(tickers=list(ticker_list),
                                                                start_date=backtest_parameters['start_date'],
                                                                stpp_date=backtest_parameters['stop_date'])
                    else:
                        print('error with parameter file')
                        HALT = True
                else:
                    HALT = True



            now = datetime.now()
            default_name = str(now)+'backtest_log.csv'

            Backtester = alpha.Engine()
            TradingStrategy = pickle.load(open(strategy_pickle_path,'rb'))
            TradingStrategy.verbose = backtest_parameters['verbose'] if 'verbose' in backtest_parameters.keys() else True

            backtest_log_file_path = backtest_parameters['csv_file_name'] if 'csv_file_name' in backtest_parameters.keys() else default_name
            log_toggle = True if 'csv_file_name' in backtest_parameters.keys() else False

            if HALT == False:
                pnl = Backtester.backtest(strategy_object=TradingStrategy,
                                          backtest_series_dictionary=backtest_data,
                                          starting_cash=float(backtest_parameters['starting_cash']),
                                          log=log_toggle,filename=backtest_log_file_path)
                did_run = True
            else: did_run = False

            print('PnL: $'+ str(round(pnl,3)) + ' | PnL %: ' + str(round((pnl/float(backtest_parameters['starting_cash']))*100,3)))
            return did_run
    def update_arguments(self,command_dict):
        if command_dict['arg_1'] in self.command_names:
            self.arguments = command_dict
            self.perform()
            return 0
        else:
            return 1

def handle_arguments(argument_dict):
    backtest = RunBacktest()
    did_run = backtest.update_arguments(argument_dict)
    if did_run == 1:
        print('unkown command', argument_dict['arg_1'])
    else: pass

def main():
    print('Welcome to Alpha Engine')

    while True:
        user_input = input('>')
        parsed_input = user_input.split(' ')
        argument_dict = {}
        for i, arg in enumerate(parsed_input):
            argument_dict['arg_' + str(i+1)] = arg

        if argument_dict['arg_1'] == '!exit':
            print('Exiting AlphaEngine')
            break

        handle_arguments(argument_dict=argument_dict)

    ''' 
    argument_dict = {}
    for i, arg in enumerate(sys.argv):
        argument_dict['arg_' + str(i)] = arg
        '''



if __name__ == "__main__":
    main()










