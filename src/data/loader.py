import pandas as pd, os
from .ccxt_client import build_exchange
def fetch_ohlcv(exchange_name: str, symbol: str, timeframe: str = '1h', limit: int = 2000):
    ex = build_exchange(exchange_name)
    data = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(data, columns=['ts','open','high','low','close','volume'])
    df['ts'] = pd.to_datetime(df['ts'], unit='ms', utc=True)
    df.set_index('ts', inplace=True)
    return df
def cache_path(cache_dir: str, exchange: str, symbol: str, timeframe: str):
    os.makedirs(cache_dir, exist_ok=True)
    key = f"{exchange}_{symbol.replace('/','-')}_{timeframe}.parquet"
    return os.path.join(cache_dir, key)
def load_or_fetch(exchange: str, symbol: str, timeframe: str, cache_dir='app_cache', limit=2000, refresh=False):
    p = cache_path(cache_dir, exchange, symbol, timeframe)
    if os.path.exists(p) and not refresh:
        return pd.read_parquet(p)
    df = fetch_ohlcv(exchange, symbol, timeframe, limit)
    df.to_parquet(p)
    return df
