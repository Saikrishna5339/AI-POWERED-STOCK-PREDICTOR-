"""
Stock Data Simulator - Generates realistic Indian market OHLCV data
Used when Yahoo Finance is rate-limited or unavailable.
All prices are based on real approximate price ranges for Indian stocks.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List


# Real approximate price ranges for Indian stocks (as of 2025)
STOCK_REFERENCE_DATA = {
    "RELIANCE": {"price": 1280, "name": "Reliance Industries Ltd", "sector": "Energy", "mc": 8.7e12},
    "TCS": {"price": 3650, "name": "Tata Consultancy Services", "sector": "IT", "mc": 13.2e12},
    "INFY": {"price": 1870, "name": "Infosys Ltd", "sector": "IT", "mc": 7.8e12},
    "HDFCBANK": {"price": 1720, "name": "HDFC Bank Ltd", "sector": "Banking", "mc": 13.1e12},
    "ICICIBANK": {"price": 1290, "name": "ICICI Bank Ltd", "sector": "Banking", "mc": 9.1e12},
    "SBIN": {"price": 810, "name": "State Bank of India", "sector": "Banking", "mc": 7.2e12},
    "WIPRO": {"price": 565, "name": "Wipro Ltd", "sector": "IT", "mc": 2.9e12},
    "HCLTECH": {"price": 1710, "name": "HCL Technologies", "sector": "IT", "mc": 4.6e12},
    "BAJFINANCE": {"price": 6820, "name": "Bajaj Finance Ltd", "sector": "Finance", "mc": 4.1e12},
    "MARUTI": {"price": 10500, "name": "Maruti Suzuki India", "sector": "Automobile", "mc": 3.4e12},
    "TATAMOTORS": {"price": 765, "name": "Tata Motors Ltd", "sector": "Automobile", "mc": 2.8e12},
    "SUNPHARMA": {"price": 1720, "name": "Sun Pharmaceutical", "sector": "Pharma", "mc": 4.1e12},
    "ITC": {"price": 472, "name": "ITC Ltd", "sector": "FMCG", "mc": 5.9e12},
    "ONGC": {"price": 265, "name": "Oil & Natural Gas Corp", "sector": "Energy", "mc": 3.3e12},
    "NTPC": {"price": 360, "name": "NTPC Ltd", "sector": "Energy", "mc": 3.5e12},
    "TITAN": {"price": 3410, "name": "Titan Company Ltd", "sector": "FMCG", "mc": 3.0e12},
    "BHARTIARTL": {"price": 1630, "name": "Bharti Airtel Ltd", "sector": "Telecom", "mc": 9.7e12},
    "ADANIENT": {"price": 2140, "name": "Adani Enterprises", "sector": "Energy", "mc": 2.4e12},
    "KOTAKBANK": {"price": 2020, "name": "Kotak Mahindra Bank", "sector": "Banking", "mc": 4.0e12},
    "ASIANPAINT": {"price": 2390, "name": "Asian Paints Ltd", "sector": "FMCG", "mc": 2.3e12},
    "TECHM": {"price": 1720, "name": "Tech Mahindra Ltd", "sector": "IT", "mc": 1.6e12},
    "HINDALCO": {"price": 680, "name": "Hindalco Industries", "sector": "Metals", "mc": 1.5e12},
    "DRREDDY": {"price": 6650, "name": "Dr. Reddys Laboratories", "sector": "Pharma", "mc": 1.1e12},
    "POWERGRID": {"price": 310, "name": "Power Grid Corp", "sector": "Energy", "mc": 2.9e12},
    "M&M": {"price": 2960, "name": "Mahindra & Mahindra", "sector": "Automobile", "mc": 3.7e12},
    "BAJAJFINSV": {"price": 1645, "name": "Bajaj Finserv", "sector": "Finance", "mc": 2.6e12},
    "NESTLEIND": {"price": 2280, "name": "Nestle India", "sector": "FMCG", "mc": 2.2e12},
    "BPCL": {"price": 278, "name": "Bharat Petroleum Corp", "sector": "Energy", "mc": 1.2e12},
    "GRASIM": {"price": 2640, "name": "Grasim Industries", "sector": "Metals", "mc": 1.7e12},
    "COALINDIA": {"price": 400, "name": "Coal India Ltd", "sector": "Energy", "mc": 2.5e12},
}

# Index reference data
INDEX_REFERENCE = {
    "^NSEI": {"name": "NIFTY 50", "price": 22400, "vol": 150},
    "^BSESN": {"name": "SENSEX", "price": 73800, "vol": 180},
    "^NSEBANK": {"name": "BANK NIFTY", "price": 47200, "vol": 250},
    "^CNXIT": {"name": "NIFTY IT", "price": 36800, "vol": 200},
    "^CNXAUTO": {"name": "NIFTY AUTO", "price": 22800, "vol": 180},
    "^CNXPHARMA": {"name": "NIFTY PHARMA", "price": 21400, "vol": 160},
}


def _get_base_price(ticker: str) -> dict:
    """Get base price and metadata for a ticker"""
    clean = ticker.upper().replace(".NS", "").replace(".BO", "")
    if clean in STOCK_REFERENCE_DATA:
        return STOCK_REFERENCE_DATA[clean]
    # Generate reasonable defaults for unknown tickers
    seed = sum(ord(c) for c in clean)
    np.random.seed(seed)
    return {
        "price": np.random.uniform(200, 3000),
        "name": f"{clean} Ltd",
        "sector": "N/A",
        "mc": np.random.uniform(1e11, 1e13),
    }


def simulate_ohlcv(ticker: str, days: int = 365, volatility: float = 0.015) -> pd.DataFrame:
    """
    Generate realistic OHLCV data using Geometric Brownian Motion + trends
    
    Args:
        ticker: stock ticker
        days: number of trading days
        volatility: daily volatility (default ~1.5%)
    
    Returns:
        DataFrame with Date, Open, High, Low, Close, Volume columns
    """
    ref = _get_base_price(ticker)
    base_price = ref["price"]
    
    # Reproducible randomness based on ticker
    seed = sum(ord(c) for c in ticker.upper().replace(".NS", ""))
    rng = np.random.default_rng(seed)
    
    # Generate business days
    end_date = datetime.now()
    dates = []
    d = end_date - timedelta(days=days * 1.5)
    while len(dates) < days and d <= end_date:
        if d.weekday() < 5:  # Mon-Fri
            dates.append(d)
        d += timedelta(days=1)
    dates = dates[-days:]
    
    # GBM simulation
    drift = rng.uniform(0.0001, 0.0004)  # slight upward bias for Indian market
    daily_vol = volatility + rng.uniform(-0.005, 0.005)
    
    returns = rng.normal(drift, daily_vol, days)
    # Add some momentum and mean reversion
    for i in range(1, days):
        if abs(returns[i-1]) > 0.03:  # mean reversion after big moves
            returns[i] *= 0.6
    
    prices = [base_price * 0.8]  # Start below current
    for r in returns:
        prices.append(prices[-1] * (1 + r))
    prices = prices[1:]
    
    # Generate OHLCV
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        intraday_range = close * rng.uniform(0.005, 0.025)
        open_price = close * (1 + rng.normal(0, 0.005))
        high = max(open_price, close) + rng.uniform(0, intraday_range)
        low = min(open_price, close) - rng.uniform(0, intraday_range)
        volume = int(rng.uniform(1e6, 1e7) * (ref.get("mc", 1e12) / 1e12))
        
        data.append({
            "Date": date,
            "Open": round(open_price, 2),
            "High": round(high, 2),
            "Low": round(max(low, 1), 2),
            "Close": round(close, 2),
            "Volume": max(volume, 100000),
        })
    
    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def simulate_stock_info(ticker: str) -> dict:
    """Generate realistic stock info dict - price matches OHLCV last close"""
    ref = _get_base_price(ticker)
    norm_ticker = ticker.upper().replace(".NS", "").replace(".BO", "")

    # Get the last close from OHLCV so prices are ALWAYS consistent
    # across /api/stock/ and /api/predict/ endpoints
    df = simulate_ohlcv(ticker, days=252)
    last_close = float(df["Close"].iloc[-1])
    prev_close  = float(df["Close"].iloc[-2]) if len(df) > 1 else last_close

    current = round(last_close, 2)
    change  = round(current - prev_close, 2)
    change_pct = round((change / prev_close) * 100, 2) if prev_close else 0

    day_high = float(df["High"].iloc[-1])
    day_low  = float(df["Low"].iloc[-1])
    open_p   = float(df["Open"].iloc[-1])

    return {
        "ticker": f"{norm_ticker}.NS",
        "name": ref["name"],
        "sector": ref.get("sector", "N/A"),
        "industry": ref.get("sector", "N/A"),
        "current_price": current,
        "previous_close": round(prev_close, 2),
        "open_price": round(open_p, 2),
        "day_high": round(day_high, 2),
        "day_low": round(day_low, 2),
        "volume": int(df["Volume"].iloc[-1]),
        "market_cap": int(ref.get("mc", 1e12)),
        "pe_ratio": round(float(np.random.default_rng(sum(ord(c) for c in norm_ticker)).uniform(12, 45)), 2),
        "pb_ratio": round(float(np.random.default_rng(sum(ord(c) for c in norm_ticker) + 1).uniform(1.5, 8.0)), 2),
        "dividend_yield": round(float(np.random.default_rng(sum(ord(c) for c in norm_ticker) + 2).uniform(0.5, 3.5)), 2),
        "week52_high": round(float(df["High"].max()), 2),
        "week52_low":  round(float(df["Low"].min()), 2),
        "change": change,
        "change_pct": change_pct,
        "currency": "INR",
        "exchange": "NSE",
        "description": f"{ref['name']} is a leading Indian company listed on NSE.",
    }


def simulate_index_data() -> List[dict]:
    """Generate index data"""
    rng = np.random.default_rng(int(datetime.now().strftime("%H%M")))
    results = []
    for symbol, ref in INDEX_REFERENCE.items():
        change_pct = float(rng.uniform(-1.5, 1.5))
        price = ref["price"] * (1 + change_pct / 100)
        results.append({
            "symbol": symbol,
            "name": ref["name"],
            "price": round(price, 2),
            "change": round(price * change_pct / 100, 2),
            "change_pct": round(change_pct, 2),
        })
    return results


def simulate_period_to_days(period: str) -> int:
    """Convert period string to number of trading days"""
    mapping = {
        "1d": 1, "5d": 5, "1mo": 22, "3mo": 66,
        "6mo": 132, "1y": 252, "2y": 504, "5y": 1260, "max": 2520,
    }
    return mapping.get(period, 252)
