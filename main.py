import os
import time
import logging
from binance.client import Client
from binance.enums import *
import ta
import pandas as pd
import requests

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
client = Client(API_KEY, API_SECRET)
client.FUTURES_URL = 'https://testnet.binancefuture.com'

PAIR_LIST = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]
TRADE_AMOUNT = 10  # USDT por trade

def get_klines(symbol, interval='5m', limit=100):
    try:
        klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close',
                                           'volume', 'close_time', 'qav', 'num_trades',
                                           'taker_base_vol', 'taker_quote_vol', 'ignore'])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        return df
    except Exception as e:
        logging.error(f"Erro ao buscar klines: {e}")
        return None

def apply_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['ema'] = ta.trend.EMAIndicator(df['close'], window=14).ema_indicator()
    df['sma'] = ta.trend.SMAIndicator(df['close'], window=28).sma_indicator()
    return df

def signal_generator(df):
    latest = df.iloc[-1]
    if latest['rsi'] < 30 and latest['close'] > latest['ema'] > latest['sma']:
        return "BUY"
    elif latest['rsi'] > 70 and latest['close'] < latest['ema'] < latest['sma']:
        return "SELL"
    return None

def execute_trade(symbol, side):
    try:
        order = client.futures_create_order(
            symbol=symbol,
            side=SIDE_BUY if side == "BUY" else SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=round(TRADE_AMOUNT / float(client.futures_mark_price(symbol=symbol)["markPrice"]), 3)
        )
        print(f"✅ {side} em {symbol} executado.")
    except Exception as e:
        logging.error(f"Erro ao executar trade: {e}")

while True:
    for symbol in PAIR_LIST:
        df = get_klines(symbol)
        if df is not None:
            df = apply_indicators(df)
            signal = signal_generator(df)
            if signal:
                execute_trade(symbol, signal)
            print(f"{symbol} | RSI: {df['rsi'].iloc[-1]:.2f} | EMA: {df['ema'].iloc[-1]:.2f} | SMA: {df['sma'].iloc[-1]:.2f}")
    time.sleep(60)