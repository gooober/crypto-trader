import asyncio
from typing import Tuple
import pandas as pd
import httpx

COINBASE_PRODUCT_MAP = {
    "BTC-USD": "BTC-USD",
    "ETH-USD": "ETH-USD",
    "SOL-USD": "SOL-USD",
}

async def fetch_coinbase_candles(symbol: str, granularity: int = 60, limit: int = 600) -> pd.DataFrame:
    """Coinbase products candles endpoint (legacy). granularity in seconds (e.g., 60 -> one minute)."""
    prod = COINBASE_PRODUCT_MAP.get(symbol, symbol)
    url = f"https://api.exchange.coinbase.com/products/{prod}/candles?granularity={granularity}"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()  # list of [time, low, high, open, close, volume]
    df = pd.DataFrame(data, columns=["time","low","high","open","close","volume"])
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.sort_values("time").tail(limit).reset_index(drop=True)
    df = df[["time","open","high","low","close","volume"]].astype(float, errors="ignore")
    return df

async def fetch_kraken_candles(symbol: str, interval: int = 1, limit: int = 600) -> pd.DataFrame:
    pair = symbol.replace("-", "")
    url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        r.raise_for_status()
        js = r.json()
    key = next(iter(js["result"].keys()))
    rows = js["result"][key][-limit:]
    df = pd.DataFrame(rows, columns=["time","open","high","low","close","vwap","volume","count"])
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df[["time","open","high","low","close","volume"]].astype(float, errors="ignore")
    return df

async def get_candles(symbol: str, limit: int = 600) -> Tuple[pd.DataFrame, str]:
    try:
        df = await fetch_coinbase_candles(symbol, 60, limit)
        return df, "coinbase"
    except Exception:
        try:
            df = await fetch_kraken_candles(symbol, 1, limit)
            return df, "kraken"
        except Exception:
            # Simulated random-walk fallback offline
            import numpy as np
            t = pd.date_range(end=pd.Timestamp.utcnow(), periods=limit, freq="1min")
            prices = 100 + np.cumsum(np.random.normal(0, 0.2, size=limit))
            highs = prices + np.random.uniform(0, 0.15, size=limit)
            lows = prices - np.random.uniform(0, 0.15, size=limit)
            opens = prices + np.random.uniform(-0.05, 0.05, size=limit)
            vols = np.random.uniform(10, 100, size=limit)
            df = pd.DataFrame({"time": t, "open": opens, "high": highs, "low": lows, "close": prices, "volume": vols})
            return df, "simulated"
