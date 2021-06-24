import yfinance as yf
import pandas as pd
def get_close_prices_yahoo(tickers, start_date, stop_date):
  '''
  get close prices for securities listed in asset_list
  :param asset_list:
  :return:
  '''
  asset_dict = {}
  for asset in tickers:
    df = pd.DataFrame()
    current_asset = yf.Ticker(asset)
    ohclv_bars = current_asset.history(start=start_date, end=stop_date)
    asset_dict[asset] = ohclv_bars
  return asset_dict
