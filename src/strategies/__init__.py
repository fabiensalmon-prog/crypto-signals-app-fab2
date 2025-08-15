from .ema_trend import ema_trend_signal
from .rsi_reversion import rsi_reversion_signal
from .composite import composite_signal
ALL = {
    'EMA Trend': ema_trend_signal,
    'RSI Mean-Reversion': rsi_reversion_signal,
    'Composite (vote)': composite_signal
}
