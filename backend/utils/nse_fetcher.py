"""
NSE India Real-Time Data Fetcher
Fetches live stock quotes from NSE India (nseindia.com) - no API key required.
This is the primary data source since Yahoo Finance is often rate-limited.
"""
import requests
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional


NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    # NOTE: Do NOT set Accept-Encoding manually - requests handles decompression
    # automatically. Setting it manually bypasses auto-decompression and breaks JSON parsing.
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive",
}

# NSE sector mapping
NSE_SECTOR_MAP = {
    "Private Sector Bank": "Banking",
    "Public Sector Bank": "Banking",
    "IT-Software": "IT",
    "Computers - Software": "IT",
    "Refineries": "Energy",
    "Oil Exploration": "Energy",
    "Pharmaceuticals": "Pharma",
    "Auto": "Automobile",
    "FMCG": "FMCG",
    "Diversified": "Conglomerate",
    "Telecom": "Telecom",
    "Finance": "Finance",
    "Metals & Mining": "Metals",
    "Power": "Energy",
    "Cement": "Infrastructure",
    "Infrastructure": "Infrastructure",
    "Gas": "Energy",
    "Retail": "Retail",
    "Insurance": "Finance",
    "Capital Goods": "Manufacturing",
    "Chemicals": "Chemicals",
}


def _fresh_nse_session() -> requests.Session:
    """
    Create a brand new requests.Session with NSE homepage cookies.
    NSE API requires cookies from the homepage to return data.
    This approach matches exactly what works in standalone tests.
    """
    s = requests.Session()
    s.headers.update(NSE_HEADERS)
    try:
        s.get("https://www.nseindia.com/", timeout=12)
        time.sleep(0.4)  # let cookies settle
    except Exception:
        pass
    return s


class NSEFetcher:
    """
    Fetches real-time Indian stock data from NSE India.
    Uses fresh sessions per quote call to ensure valid cookies.
    """

    def __init__(self):
        self._quote_cache: Dict = {}
        self._cache_ttl: Dict = {}
        self._index_cache: Optional[List] = None
        self._index_cache_time: float = 0

    def get_quote(self, symbol: str) -> Optional[Dict]:
        """
        Fetch live quote for an NSE stock symbol.
        Returns dict with current_price, change, change_pct, etc.
        Returns None if unavailable.
        """
        symbol = symbol.upper().replace(".NS", "").replace(".BO", "")

        # Check cache (2 min TTL for live prices)
        cache_key = f"quote_{symbol}"
        now = time.time()
        if cache_key in self._quote_cache:
            if now - self._cache_ttl.get(cache_key, 0) < 120:
                return self._quote_cache[cache_key]

        try:
            # Create fresh session with homepage cookies - this is the proven approach
            session = _fresh_nse_session()
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            r = session.get(url, timeout=12)

            if not r.content or len(r.content.strip()) < 10:
                print(f"[NSE] Empty response for {symbol}")
                return None

            if r.status_code != 200:
                print(f"[NSE] HTTP {r.status_code} for {symbol}")
                return None

            data = r.json()
            price_info = data.get("priceInfo", {})
            metadata = data.get("metadata", {})
            sec_info = data.get("securityInfo", {})
            industry_info = data.get("industryInfo", {})

            last_price = price_info.get("lastPrice") or price_info.get("close")
            if not last_price:
                return None

            prev_close = price_info.get("previousClose") or last_price
            change = price_info.get("change") or (last_price - prev_close)
            change_pct = price_info.get("pChange") or ((change / prev_close * 100) if prev_close else 0)

            intraday = price_info.get("intraDayHighLow", {})
            week_hl = price_info.get("weekHighLow", {})

            company_name = (
                metadata.get("companyName")
                or sec_info.get("companyName")
                or data.get("info", {}).get("companyName")
                or f"{symbol} Ltd"
            )

            raw_industry = (
                industry_info.get("basicIndustry")
                or industry_info.get("industry")
                or metadata.get("industry")
                or "N/A"
            )
            sector = NSE_SECTOR_MAP.get(
                raw_industry,
                raw_industry.split(" ")[0] if raw_industry != "N/A" else "N/A"
            )

            mktcap = metadata.get("marketCap") or 0
            if isinstance(mktcap, str):
                try:
                    mktcap = float(mktcap.replace(",", "")) * 1e7
                except Exception:
                    mktcap = 0

            volume = metadata.get("totalTradedVolume") or 0
            if isinstance(volume, str):
                try:
                    volume = int(volume.replace(",", ""))
                except Exception:
                    volume = 0

            result = {
                "ticker": f"{symbol}.NS",
                "name": company_name,
                "sector": sector,
                "industry": raw_industry,
                "current_price": round(float(last_price), 2),
                "previous_close": round(float(prev_close), 2),
                "open_price": round(float(price_info.get("open", prev_close) or prev_close), 2),
                "day_high": round(float(intraday.get("max") or price_info.get("high") or last_price), 2),
                "day_low": round(float(intraday.get("min") or price_info.get("low") or last_price), 2),
                "volume": int(volume),
                "market_cap": int(mktcap),
                "pe_ratio": round(float(metadata.get("pdSymbolPe") or 0), 2),
                "pb_ratio": 0,
                "dividend_yield": 0,
                "week52_high": round(float(week_hl.get("max") or last_price * 1.3), 2),
                "week52_low": round(float(week_hl.get("min") or last_price * 0.7), 2),
                "change": round(float(change), 2),
                "change_pct": round(float(change_pct), 2),
                "currency": "INR",
                "exchange": "NSE",
                "description": f"{company_name} is listed on the National Stock Exchange of India.",
                "_source": "NSE_LIVE",
            }

            self._quote_cache[cache_key] = result
            self._cache_ttl[cache_key] = time.time()
            print(f"[NSE] LIVE {symbol} = Rs{result['current_price']} ({result['change_pct']:+.2f}%)")
            return result

        except Exception as e:
            print(f"[NSE] Quote failed for {symbol}: {e}")
            return None

    def get_historical_ohlcv(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from NSE India.
        Returns DataFrame with Date, Open, High, Low, Close, Volume.
        """
        symbol = symbol.upper().replace(".NS", "").replace(".BO", "")

        try:
            session = _fresh_nse_session()
            end_date = datetime.now()
            start_date = end_date - timedelta(days=int(days * 1.5))
            end_str = end_date.strftime("%d-%m-%Y")
            start_str = start_date.strftime("%d-%m-%Y")

            url = f"https://www.nseindia.com/api/historical/cm/equity?symbol={symbol}&series=[%22EQ%22]&from={start_str}&to={end_str}&csv=true"
            r = session.get(url, timeout=15)

            if r.status_code == 200 and r.content:
                from io import StringIO
                df = pd.read_csv(StringIO(r.text))
                if len(df) > 5:
                    col_map = {
                        "Date": "Date", "CH_TIMESTAMP": "Date",
                        "Open Price": "Open", "CH_OPENING_PRICE": "Open",
                        "High Price": "High", "CH_TRADE_HIGH_PRICE": "High",
                        "Low Price": "Low", "CH_TRADE_LOW_PRICE": "Low",
                        "Close Price": "Close", "CH_CLOSING_PRICE": "Close",
                        "Total Traded Quantity": "Volume", "CH_TOT_TRADED_QTY": "Volume",
                    }
                    df = df.rename(columns=col_map)
                    if "Close" in df.columns and "Date" in df.columns:
                        needed = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in df.columns]
                        df = df[needed].copy()
                        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
                        df = df.dropna(subset=["Date", "Close"])
                        for col in ["Open", "High", "Low", "Close"]:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")
                        if "Volume" in df.columns:
                            df["Volume"] = pd.to_numeric(df["Volume"].astype(str).str.replace(",", ""), errors="coerce").fillna(0).astype(int)
                        df = df.sort_values("Date").tail(days).reset_index(drop=True)
                        if len(df) > 10:
                            print(f"[NSE] Got {len(df)} historical rows for {symbol}")
                            return df
        except Exception as e:
            print(f"[NSE] Historical failed for {symbol}: {e}")

        return pd.DataFrame()

    def get_indices(self) -> List[Dict]:
        """Fetch NSE index data (NIFTY 50, BANK NIFTY etc.)"""
        now = time.time()
        # Cache indices for 3 minutes
        if self._index_cache and (now - self._index_cache_time) < 180:
            return self._index_cache

        try:
            session = _fresh_nse_session()
            r = session.get("https://www.nseindia.com/api/allIndices", timeout=12)
            if r.status_code == 200 and r.content:
                data = r.json()
                result = []
                for idx in data.get("data", []):
                    name = idx.get("index", "")
                    if any(n in name.upper() for n in ["NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY AUTO", "NIFTY PHARMA"]):
                        try:
                            result.append({
                                "symbol": name,
                                "name": name,
                                "price": round(float(idx.get("last", 0)), 2),
                                "change": round(float(idx.get("variation", 0)), 2),
                                "change_pct": round(float(idx.get("percentChange", 0)), 2),
                            })
                        except Exception:
                            pass
                if result:
                    self._index_cache = result[:6]
                    self._index_cache_time = now
                    return self._index_cache
        except Exception as e:
            print(f"[NSE] Indices failed: {e}")
        return []


# Singleton instance
_nse_fetcher: Optional[NSEFetcher] = None


def get_nse_fetcher() -> NSEFetcher:
    global _nse_fetcher
    if _nse_fetcher is None:
        _nse_fetcher = NSEFetcher()
    return _nse_fetcher
