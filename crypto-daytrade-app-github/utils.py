import math
import numpy as np
import pandas as pd

def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    up = (delta.where(delta > 0, 0.0)).rolling(length).mean()
    down = (-delta.where(delta < 0, 0.0)).rolling(length).mean()
    rs = up / (down + 1e-12)
    return 100 - (100 / (1 + rs))

def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df['close'].shift(1)
    high_low = df['high'] - df['low']
    high_pc = (df['high'] - prev_close).abs()
    low_pc = (df['low'] - prev_close).abs()
    return pd.concat([high_low, high_pc, low_pc], axis=1).max(axis=1)

def atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    tr = true_range(df)
    return tr.rolling(length).mean()

def vwap(df: pd.DataFrame) -> pd.Series:
    pv = (df['close'] * df['volume']).cumsum()
    vv = (df['volume']).cumsum().replace(0, np.nan)
    return pv / vv

def bollinger_bands(series: pd.Series, length: int = 20, mult: float = 2.0):
    ma = series.rolling(length).mean()
    sd = series.rolling(length).std(ddof=0)
    upper = ma + mult * sd
    lower = ma - mult * sd
    return ma, upper, lower

def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.Series:
    hl2 = (df['high'] + df['low']) / 2.0
    atr_v = atr(df, period)
    upperband = hl2 + multiplier * atr_v
    lowerband = hl2 - multiplier * atr_v

    st = pd.Series(index=df.index, dtype=float)
    direction = 1
    for i in range(len(df)):
        if i == 0:
            st.iloc[i] = lowerband.iloc[i]
            continue
        if df['close'].iloc[i] > st.iloc[i-1]:
            direction = 1
        elif df['close'].iloc[i] < st.iloc[i-1]:
            direction = -1
        if direction == 1:
            st.iloc[i] = max(lowerband.iloc[i], st.iloc[i-1])
        else:
            st.iloc[i] = min(upperband.iloc[i], st.iloc[i-1])
    return st

def swing_points(series: pd.Series, lookback: int = 5):
    highs = series.rolling(lookback, center=True).apply(lambda x: int(x.argmax() == len(x)//2), raw=True)
    lows = series.rolling(lookback, center=True).apply(lambda x: int(x.argmin() == len(x)//2), raw=True)
    last_high_idx = highs.replace(0, pd.NA).ffill().dropna().index[-1] if highs.notna().any() else None
    last_low_idx = lows.replace(0, pd.NA).ffill().dropna().index[-1] if lows.notna().any() else None
    last_high = series.loc[last_high_idx] if last_high_idx is not None else None
    last_low = series.loc[last_low_idx] if last_low_idx is not None else None
    return last_high_idx, last_high, last_low_idx, last_low

def zscore(series: pd.Series, window: int = 50) -> pd.Series:
    m = series.rolling(window).mean()
    s = series.rolling(window).std(ddof=0).replace(0, np.nan)
    return (series - m) / s

def format_usd(x: float) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x))):
        return "-"
    return f"${x:,.2f}"

def percent(x: float) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x))):
        return "-"
    return f"{x*100:.2f}%"
