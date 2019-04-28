# -*- coding: utf-8 -*-
"""Binance to CSV.

This module was created to pull historical data from Bininace, particularaly as a training set
for machine learning algorithms and backtesting models.

madified from:
https://sammchardy.github.io/binance/2018/01/08/historical-data-download-binance.html
https://steemit.com/python/@marketstack/how-to-download-historical-price-data-from-binance-with-python

Attributes:
    trading_pair (str): The trading pair to query. ("ETHUSDT")

    interval (str): The interval to query: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w

Todo:
    * Clean up plotting
    * UI?

"""

import sys
import os
import pytz
import dateparser
import time
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np     
import pandas as pd  
import json          
import requests    
import csv
import datetime as dt  

def interval_to_milliseconds(interval):
    """Convert a Binance interval string to milliseconds

    Parameters
    ----------
        interval (str): Binance interval string 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w

    Returns
    -------
        int: interval in millisecond format.
    """
    ms = None
    seconds_per_unit = {
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 24 * 60 * 60
    }

    unit = interval[-1]
    if unit in seconds_per_unit:
        try:
            ms = int(interval[:-1]) * seconds_per_unit[unit] * 1000
        except ValueError:
            pass
    return ms


def date_to_milliseconds(date_str):
    """Convert UTC date to milliseconds
    If using offset strings add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"
    See dateparse docs for formats http://dateparser.readthedocs.io/en/latest/

    Parameters
    ----------
        date_str (str): A date.

    Returns
    -------
        Dataframe: A date in millisecond format.
    """
    # get epoch value in UTC
    epoch = dt.datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
    # parse our date string
    d = dateparser.parse(date_str)
    # if the date is not timezone aware apply UTC timezone
    if d.tzinfo is None or d.tzinfo.utcoffset(d) is None:
        d = d.replace(tzinfo=pytz.utc)

    # return the difference in time
    return int((d - epoch).total_seconds() * 1000.0)


def get_bars(symbol, interval='1h', start_date="January 01, 2018", end_date="January 01, 2020"):
    """Query the Binanace API starting from a given date.

    Parameters
    ----------
        symbol (str): The first parameter.
        interval (str): The second parameter.
        start_date (str): Starting date.

    Returns
    -------
        Dataframe: Pandas dataframe of historical info
    """
    timeframe = interval_to_milliseconds(interval)
    limit = 500
    root_url = 'https://api.binance.com/api/v1/klines'
    start_ts = date_to_milliseconds(start_date)
    end_ts = date_to_milliseconds(end_date)
    data = []
    idx = 0
    while True:
        url = root_url + '?symbol=' + symbol + '&interval=' + interval + '&startTime=' + str(start_ts) + '&endTime=' + str(end_ts)
        temp_data = json.loads(requests.get(url).text)
        if data:
            data += temp_data
        else:
            data = temp_data
        if(len(temp_data)): start_ts = temp_data[len(temp_data) - 1][0] + timeframe
        if (len(temp_data) < limit):
            break
        idx += 1
        if idx % 5 == 0:
            time.sleep(.25)

    df = pd.DataFrame(data)
    df.columns = ['open_time',
                  'o', 'h', 'l', 'c', 'v',
                  'close_time', 'qav', 'num_trades',
                  'taker_base_vol', 'taker_quote_vol', 'ignore']
    df.index = [dt.datetime.fromtimestamp(x/1000.0) for x in df.close_time]
    return df

if __name__ == '__main__':
    try:
        months = mdates.MonthLocator()
        days = mdates.DayLocator()
        trading_pair = input("Trading Pair: ").upper()
        interval = input("Interval: ").lower()
        start_date = input("Start Date (DD/MM/YY'): ")
        end_date = input("End Date (DD/MM/YY'): ")
        filename = input("Filename: ")
        directory = "./Data/"+trading_pair
        data = get_bars(trading_pair, interval, start_date, end_date)
        if not os.path.exists(directory):
            os.makedirs(directory)
        data.to_csv(directory+"/"+filename+".csv", sep='\t', encoding='utf-8')

        plot = data['c'].astype('float').plot(figsize=(16, 9))
        plt.xlabel("Time: " + interval)
        plt.title(trading_pair)
        plot.xaxis.set_major_locator(months)
        plot.xaxis.set_minor_locator(days)
        plot.grid(True)
        plt.savefig(directory+"/"+filename+'.png')
    
    except KeyboardInterrupt:
        sys.exit()