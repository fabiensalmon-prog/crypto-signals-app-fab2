from .ema_trend import ema_trend_signal
from .rsi_reversion import rsi_reversion_signal
def composite_signal(df):
    s1 = ema_trend_signal(df); s2 = rsi_reversion_signal(df)
    return (s1 + s2).clip(-1,1).rename('signal')
