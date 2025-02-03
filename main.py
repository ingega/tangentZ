import pandas as pd
import numpy as np
from binance.client import Client
import data
import key  # da api_key
import requests
import time
import hashlib
import hmac


client = Client(key.api_key, key.api_secret)


class DataHandler:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def get_binance_data(self, symbol, interval, limit=1000, now_time=0):
        all_data = []
        batch_size = 1000
        interval_minutes = self.interval_to_minutes(interval)

        # Calculate initial start time (in milliseconds)
        if now_time == 0:
            end_time = int(time.time() * 1000)  # Current time in milliseconds
        else:  # time seted by user, time must be in stamTime (miliseconds)
            end_time = now_time
        start_time = end_time - (limit * interval_minutes * 60 * 1000)

        while limit > 0:
            fetch_size = min(batch_size, limit)
            url = (f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval="
                   f"{interval}&limit={fetch_size}&startTime={start_time}")
            response = requests.get(url, headers={"X-MBX-APIKEY": self.api_key})
            data = response.json()

            if not data:
                break

            all_data.extend(data)
            start_time = data[-1][0] + 1  # Update start_time to the timestamp of the last fetched entry + 1
            limit -= fetch_size

            # Respect rate limits
            time.sleep(0.2)

        df = pd.DataFrame(all_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
            'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
            'taker_buy_quote_asset_volume', 'ignore'
        ])

        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['date'] = df['timestamp']
        df['hour'] = df['date'].dt.hour

        # Convert necessary columns to numeric
        df['open'] = pd.to_numeric(df['open'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        # aditional info
        df['ticker'] = symbol
        # Fetch symbol precision
        precision = self.get_symbol_precision(symbol)
        df['precision'] = precision
        df['side'] = np.where(df['close'] > df['open'], "BUY", "SELL")
        df['size'] = abs((df['open'] - df['close']) / df['open'])

        return df

    def interval_to_minutes(self, interval):
        # Convert interval string to minutes
        if interval.endswith('m'):
            return int(interval[:-1])
        elif interval.endswith('h'):
            return int(interval[:-1]) * 60
        elif interval.endswith('d'):
            return int(interval[:-1]) * 60 * 24
        elif interval.endswith('w'):
            return int(interval[:-1]) * 60 * 24 * 7
        elif interval.endswith('M'):
            return int(interval[:-1]) * 60 * 24 * 30
        else:
            raise ValueError(f"Unsupported interval format: {interval}")

    def get_symbol_precision(self, symbol):
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        response = self.send_signed_request("GET", url)
        exchange_info = response.json()

        for s in exchange_info['symbols']:
            try:
                if s['symbol'] == symbol:
                    # Find the precision in the symbol information
                    precision = s['pricePrecision']
                    return precision
            except:  # almost is an unlisted ticker
                return 0

    def send_signed_request(self, method, url, params=None):
        if params is None:
            params = {}
        params['timestamp'] = int(time.time() * 1000)
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = hmac.new(self.api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        params['signature'] = signature
        headers = {"X-MBX-APIKEY": self.api_key}

        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        else:
            response = requests.post(url, headers=headers, params=params)

        return response


def pairs():
    d = client.futures_exchange_info()
    sym = d['symbols']
    pairs = []
    for s in sym:
        if s['quoteAsset'] == 'USDT':
            p = s['pair']
            pairs.append(p)
    # if the bar doesn't have any volume in a day bar, so let's remove it
    for pair in pairs:
        b = client.futures_klines(symbol=pair, interval="1d", limit=1)
        if b[0][5] == '0':  # zero operations
            pairs.remove(pair)
    return pairs


def get_all_pairs_opor():
    datahandler = DataHandler(key.api_key, key.api_secret)
    p = pd.read_csv('ticks.csv', header=None)
    p = p.to_dict(orient='records')
    cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
            'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
            'taker_buy_quote_asset_volume', 'ignore', 'date', 'hour', 'ticker',
            'precision', 'side', 'size'
            ]
    all = pd.DataFrame(columns=cols)  # empty df
    bars_avg = data.bars
    tangent = data.tangent
    cv = data.cv
    df_in = pd.DataFrame(columns=cols)
    for r in p:
        try:
            df = datahandler.get_binance_data(symbol=r[0], interval=data.interval, limit=bars_avg)
            df['ticker'] = r[0]
            data_tangent = (df.iloc[-1]['close'] - df.iloc[0]['close']) / df.iloc[-1]['close']
            if data_tangent > 0:
                side = "BUY"
            else:
                side = "SELL"
            data_tangent = abs(data_tangent)
            z = df['close'].std()
            data_cv = z / df.iloc[-1]['close']
            # df need the values
            df['tangent'] = data_tangent
            df['cv'] = data_cv
            df['side'] = side
            all = pd.concat([all, df], ignore_index=True)
            if data_tangent > tangent and data_cv > cv:  # let's add the row
                # the system only need the last row
                df = df.iloc[[-1]]
                df_in = pd.concat([df_in, df], ignore_index=True)

        except:
            msg = (f'there\'s an error ocurred when tried to get the info of '
                   f'{r[0]} gmtime: {time.asctime(time.gmtime())}')
            print(msg)
    # at the very end, verify all this info is needed, so, let's return the alls, and df_in data
    # so, let's send in csv by mail, but this function only create (re-writting) the csv file
    # the file is named by YY-MM-DD-HH-all-data.csv
    file_name = (f'{time.gmtime().tm_year}-{time.gmtime().tm_mon}-'
                 f'{time.gmtime().tm_mday}-{time.gmtime().tm_hour}.csv')
    # the complete filepath include the pathgan directory
    file_name = data.pathGan + file_name
    if data.debug_mode:  # in false, no file is created
        all.to_csv(file_name, columns=None)
    return {'df_in': df_in, 'path': file_name}
