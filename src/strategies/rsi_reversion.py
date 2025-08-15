import pandas as pd, numpy as np
def rsi(series: pd.Series, length:int=14):
    d = series.diff(); up = d.clip(lower=0).ewm(alpha=1/length, adjust=False).mean(); down = -d.clip(upper=0).ewm(alpha=1/length, adjust=False).mean()
    rs = up / (down + 1e-9); return 100 - 100/(1+rs)
def rsi_reversion_signal(df: pd.DataFrame, length:int=14, lo:int=30, hi:int=70):
    r = rsi(df['close'], length); return ((r<lo).astype(int) - (r>hi).astype(int)).clip(-1,1).rename('signal')
