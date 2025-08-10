import pandas as pd
from utils import ema, rsi, vwap, atr, bollinger_bands, supertrend, swing_points, zscore

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out['ema9'] = ema(out['close'], 9)
    out['ema21'] = ema(out['close'], 21)
    out['rsi14'] = rsi(out['close'], 14)
    out['vwap'] = vwap(out)
    out['atr14'] = atr(out, 14)
    mid, up, lo = bollinger_bands(out['close'], 20, 2.0)
    out['bb_mid'] = mid
    out['bb_up'] = up
    out['bb_lo'] = lo
    out['st'] = supertrend(out, 10, 3.0)
    out['vwap_z'] = zscore(out['close'] - out['vwap'], 50)
    return out

def generate_signal(df: pd.DataFrame):
    row = df.iloc[-1]
    votes = []
    rationale = []

    # EMA crossover + slope filter
    ema_bias = "bull" if row['ema9'] > row['ema21'] else ("bear" if row['ema9'] < row['ema21'] else "flat")
    slope_ok = (df['ema9'].iloc[-1] - df['ema9'].iloc[-3]) > 0 if ema_bias == "bull" else (df['ema9'].iloc[-1] - df['ema9'].iloc[-3]) < 0
    if ema_bias == "bull" and slope_ok: votes.append(1); rationale.append("EMA9>EMA21 ↑")
    elif ema_bias == "bear" and slope_ok: votes.append(-1); rationale.append("EMA9<EMA21 ↓")

    # RSI
    if row['rsi14'] > 55: votes.append(1); rationale.append(f"RSI {row['rsi14']:.0f} strong")
    elif row['rsi14'] < 45: votes.append(-1); rationale.append(f"RSI {row['rsi14']:.0f} weak")

    # VWAP bias
    if row['close'] > row['vwap']: votes.append(1); rationale.append("Above VWAP")
    else: votes.append(-1); rationale.append("Below VWAP")

    # SuperTrend
    if row['close'] >= row['st']: votes.append(1); rationale.append("SuperTrend up")
    else: votes.append(-1); rationale.append("SuperTrend down")

    # BB regime
    bb_width = (row['bb_up'] - row['bb_lo']) / row['bb_mid'] if row['bb_mid'] else 0
    if bb_width < 0.01: rationale.append("Squeeze")
    else: rationale.append("Expanded")

    score = sum(votes)
    if score >= 2: signal = "BUY"
    elif score <= -2: signal = "SELL"
    else: signal = "NEUTRAL"

    return {"signal": signal, "score": score, "rationale": "; ".join(rationale)}

def stop_price(model: str, df: pd.DataFrame, side: str, atr_mult: float = 1.5):
    last = df.iloc[-1]
    if model == "ATR":
        return (last['close'] - atr_mult * last['atr14']) if side == "BUY" else (last['close'] + atr_mult * last['atr14'])
    elif model == "SuperTrend":
        return last['st']
    elif model == "Structure":
        _, _, _, last_low = swing_points(df['close'], 5)
        if side == "BUY":
            return last_low if last_low else last['close'] - last['atr14']
        else:
            return last['close'] + last['atr14']
    elif model == "Fixed%":
        pct = 0.005
        return last['close'] * (1 - pct) if side == "BUY" else last['close'] * (1 + pct)
    return None
