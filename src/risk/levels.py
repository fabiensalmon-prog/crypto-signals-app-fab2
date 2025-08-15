import pandas as pd, numpy as np
def atr(df: pd.DataFrame, length: int = 14):
    hl = df['high'] - df['low']; hc = (df['high'] - df['close'].shift()).abs(); lc = (df['low'] - df['close'].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.ewm(span=length, adjust=False).mean()
def adaptive_levels(df: pd.DataFrame, direction: int, atr_mult_sl=2.5, atr_mult_tp=3.5, trail_start_R=1.0, trail_atr_mult=2.0):
    if direction == 0 or len(df)<2: return None
    a = float(atr(df, 14).iloc[-1]); price = float(df['close'].iloc[-1])
    if direction>0: sl = price - atr_mult_sl*a; tp = price + atr_mult_tp*a
    else: sl = price + atr_mult_sl*a; tp = price - atr_mult_tp*a
    return {'entry': price, 'sl': sl, 'tp': tp, 'atr': a, 'trail_start_R': trail_start_R, 'trail_atr_mult': trail_atr_mult}
def risk_position_size(account_equity: float, entry: float, stop: float, risk_pct: float, contract_value: float = 1.0):
    risk_amt = account_equity * (risk_pct/100.0)
    per_unit_loss = abs(entry - stop) * contract_value / max(entry, 1e-9)
    qty = 0.0 if per_unit_loss==0 else risk_amt / per_unit_loss
    return max(qty, 0.0)
