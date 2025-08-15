import pandas as pd, numpy as np
def backtest(df, signal, initial_cash=10000, fee_bps=2.5, slippage_bps=1.0):
    ret = df['close'].pct_change().fillna(0.0)
    pos = signal.shift().fillna(0.0).clip(-1,1)
    cost = (pos.diff().abs().fillna(0.0)) * (fee_bps+slippage_bps)/10000.0
    pnl = pos*ret - cost
    equity = initial_cash*(1+pnl).cumprod()
    return pd.DataFrame({'ret': ret, 'pos': pos, 'pnl': pnl, 'equity': equity}, index=df.index)
