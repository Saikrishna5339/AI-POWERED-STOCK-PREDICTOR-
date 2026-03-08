"""
Enhanced data fetching module for Indian stock market (NSE/BSE)
Primary source: NSE India live API (real-time prices, no API key needed)
Fallback chain: NSE India -> Yahoo Finance -> Simulator
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta
import time
import requests
from backend.config import NEWSAPI_KEY, NSE_SUFFIX
from backend.utils.stock_simulator import (
    simulate_ohlcv,
    simulate_stock_info,
    simulate_index_data,
    simulate_period_to_days,
    STOCK_REFERENCE_DATA,
    INDEX_REFERENCE,
)
from backend.utils.nse_fetcher import get_nse_fetcher


class DataFetcher:
    """Fetches stock data for Indian market stocks (live or simulated)"""

    def __init__(self):
        self.newsapi_key = NEWSAPI_KEY
        self._cache: Dict = {}
        self._cache_ttl: Dict = {}
        self._yf_working: bool = False  # Assume blocked; set True if fetch succeeds

    def normalize_ticker(self, ticker: str) -> str:
        """Add .NS suffix for Indian stocks if not already present"""
        ticker = ticker.upper().strip()
        if "." not in ticker:
            return ticker + NSE_SUFFIX
        return ticker

    def _try_yf_download(self, ticker_ns: str, period: str) -> pd.DataFrame:
        """Try fetching via yfinance with timeout"""
        try:
            stock = yf.Ticker(ticker_ns)
            df = stock.history(period=period, auto_adjust=True, timeout=8)
            if df is not None and not df.empty:
                self._yf_working = True
                return df
        except Exception as e:
            err = str(e)
            if "429" in err or "Too Many" in err or "Expecting value" in err:
                self._yf_working = False
        return pd.DataFrame()

    # ─── Core: fetch OHLCV ────────────────────────────────────
    def fetch_stock_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """
        Fetch historical OHLCV data.
        Priority: NSE historical -> Yahoo Finance -> Simulator anchored to NSE live price
        """
        cache_key = f"ohlcv_{ticker}_{period}"
        if cache_key in self._cache:
            if time.time() - self._cache_ttl.get(cache_key, 0) < 300:
                return self._cache[cache_key]

        norm = self.normalize_ticker(ticker)
        df = pd.DataFrame()

        # ── 1. Try NSE India historical ───────────────────────
        try:
            nse = get_nse_fetcher()
            days = simulate_period_to_days(period)
            nse_df = nse.get_historical_ohlcv(ticker, days=days)
            if nse_df is not None and not nse_df.empty and len(nse_df) > 10:
                df = nse_df
                print(f"[DataFetcher] NSE historical: {len(df)} rows for {ticker}")
        except Exception as e:
            print(f"[DataFetcher] NSE historical failed: {e}")

        # ── 2. Try Yahoo Finance ──────────────────────────────
        if df.empty and self._yf_working:
            df = self._try_yf_download(norm, period)
            if df.empty:
                bse = norm.replace(".NS", ".BO")
                df = self._try_yf_download(bse, period)

        # ── 3. Simulator fallback (anchored to NSE live price) ─
        if df.empty:
            days = simulate_period_to_days(period)
            df = simulate_ohlcv(ticker, days=days)

            # Anchor simulator's last close to NSE live price so charts
            # match the live price shown in the dashboard
            try:
                nse = get_nse_fetcher()
                live = nse.get_quote(ticker)
                if live and live.get("current_price"):
                    live_price = float(live["current_price"])
                    sim_last = float(df["Close"].iloc[-1])
                    if sim_last > 0:
                        scale = live_price / sim_last
                        for col in ["Open", "High", "Low", "Close"]:
                            df[col] = (df[col] * scale).round(2)
                        print(f"[DataFetcher] Anchored {ticker} sim to NSE {live_price} (scale={scale:.3f})")
            except Exception:
                pass
        else:
            df.reset_index(inplace=True)
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
            df = df.dropna(subset=["Close"])

        self._cache[cache_key] = df
        self._cache_ttl[cache_key] = time.time()
        return df

    # ─── Stock Info ───────────────────────────────────────────
    def fetch_stock_info(self, ticker: str) -> Dict:
        """
        Fetch comprehensive stock info.
        Priority: NSE India live API -> Yahoo Finance -> Simulator
        """
        cache_key = f"info_{ticker}"
        if cache_key in self._cache:
            if time.time() - self._cache_ttl.get(cache_key, 0) < 120:
                return self._cache[cache_key]

        norm = self.normalize_ticker(ticker)
        result = None

        # ── 1. Try NSE India real-time API (primary) ──────────
        try:
            nse = get_nse_fetcher()
            nse_data = nse.get_quote(ticker)
            if nse_data and nse_data.get("current_price"):
                result = nse_data
                print(f"[DataFetcher] NSE LIVE: {ticker} = Rs{nse_data['current_price']}")
        except Exception as nse_err:
            print(f"[DataFetcher] NSE failed for {ticker}: {nse_err}")

        # ── 2. Try Yahoo Finance (fallback) ───────────────────
        if result is None and self._yf_working:
            try:
                df_1y = self._try_yf_download(norm, "1y")
                df_2d = self._try_yf_download(norm, "2d")

                if not df_1y.empty:
                    current = float(df_1y["Close"].iloc[-1])
                    prev = float(df_1y["Close"].iloc[-2]) if len(df_1y) >= 2 else current
                    change = current - prev
                    change_pct = (change / prev * 100) if prev else 0

                    if not df_2d.empty:
                        oday = float(df_2d["Open"].iloc[-1])
                        dhigh = float(df_2d["High"].iloc[-1])
                        dlow = float(df_2d["Low"].iloc[-1])
                        vol = int(df_2d["Volume"].iloc[-1])
                    else:
                        oday = dhigh = dlow = current
                        vol = 0

                    name = norm.replace(".NS", "")
                    sector = "N/A"
                    mc = 0
                    pe = 0
                    try:
                        info = yf.Ticker(norm).info
                        name = info.get("longName", name) or name
                        sector = info.get("sector", "N/A") or "N/A"
                        mc = info.get("marketCap", 0) or 0
                        pe = round(float(info.get("trailingPE", 0) or 0), 2)
                    except Exception:
                        pass

                    result = {
                        "ticker": norm,
                        "name": name,
                        "sector": sector,
                        "industry": sector,
                        "current_price": round(current, 2),
                        "previous_close": round(prev, 2),
                        "open_price": round(oday, 2),
                        "day_high": round(dhigh, 2),
                        "day_low": round(dlow, 2),
                        "volume": vol,
                        "market_cap": mc,
                        "pe_ratio": pe,
                        "pb_ratio": 0,
                        "dividend_yield": 0,
                        "week52_high": round(float(df_1y["High"].max()), 2),
                        "week52_low": round(float(df_1y["Low"].min()), 2),
                        "change": round(change, 2),
                        "change_pct": round(change_pct, 2),
                        "currency": "INR",
                        "exchange": "NSE",
                        "description": "",
                    }
            except Exception:
                pass

        # ── 3. Simulator fallback ─────────────────────────────
        if result is None:
            result = simulate_stock_info(ticker)

        self._cache[cache_key] = result
        self._cache_ttl[cache_key] = time.time()
        return result

    # ─── OHLCV for charts ─────────────────────────────────────
    def fetch_ohlcv(self, ticker: str, period: str = "1y") -> List[Dict]:
        """Fetch OHLCV formatted for candlestick charts"""
        df = self.fetch_stock_data(ticker, period)
        result = []
        for _, row in df.iterrows():
            result.append({
                "date": str(row["Date"])[:10],
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })
        return result

    # ─── Current Price ────────────────────────────────────────
    def get_current_price(self, ticker: str) -> float:
        """Get current stock price"""
        try:
            info = self.fetch_stock_info(ticker)
            return float(info["current_price"])
        except Exception:
            ref = simulate_stock_info(ticker)
            return float(ref["current_price"])

    # ─── News ─────────────────────────────────────────────────
    def fetch_news(self, ticker: str, num_articles: int = 10) -> List[Dict]:
        """Fetch latest financial news for a stock (NewsAPI or mock)"""
        clean = ticker.replace(".NS", "").replace(".BO", "")
        info_key = f"info_{ticker}"
        company_name = self._cache.get(info_key, {}).get("name", clean)

        if not self.newsapi_key or self.newsapi_key in ("your_newsapi_key_here", ""):
            return self._get_mock_news(clean, company_name)

        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": f"{company_name} OR {clean} NSE stock India",
                "from": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "to": datetime.now().strftime("%Y-%m-%d"),
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": num_articles,
                "apiKey": self.newsapi_key,
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            articles = []
            for a in response.json().get("articles", [])[:num_articles]:
                if a.get("title") and "[Removed]" not in a.get("title", ""):
                    articles.append({
                        "title": a.get("title", ""),
                        "description": a.get("description", ""),
                        "url": a.get("url", ""),
                        "publishedAt": a.get("publishedAt", ""),
                        "source": a.get("source", {}).get("name", ""),
                    })
            return articles or self._get_mock_news(clean, company_name)
        except Exception:
            return self._get_mock_news(clean, company_name)

    def _get_mock_news(self, ticker: str, company_name: str) -> List[Dict]:
        now = datetime.now()
        mc = company_name
        return [
            {"title": f"{mc} Reports Strong Q3 Earnings Beat", "description": f"{mc} beat analyst estimates with strong revenue growth.", "url": "#", "publishedAt": now.isoformat(), "source": "Economic Times"},
            {"title": f"Analysts Upgrade {ticker} to BUY on Growth Prospects", "description": f"Multiple brokerages raised target price for {mc} citing strong fundamentals.", "url": "#", "publishedAt": (now-timedelta(hours=4)).isoformat(), "source": "Moneycontrol"},
            {"title": f"{mc} Expands into New Markets, Investors Optimistic", "description": f"{mc} announced strategic expansion plans targeting new market opportunities.", "url": "#", "publishedAt": (now-timedelta(hours=12)).isoformat(), "source": "Business Standard"},
            {"title": f"NSE Sees {ticker} Among Top Gainers This Session", "description": f"{ticker} led market gains with strong institutional interest.", "url": "#", "publishedAt": (now-timedelta(days=1)).isoformat(), "source": "Mint"},
            {"title": f"{mc} Management Upbeat on Future Earnings Outlook", "description": f"Company confident about achieving growth targets for upcoming financial year.", "url": "#", "publishedAt": (now-timedelta(days=2)).isoformat(), "source": "CNBC TV18"},
            {"title": f"FII Buying Seen in {ticker} Amid Market Recovery", "description": f"Foreign institutions accumulated positions in {mc} this week.", "url": "#", "publishedAt": (now-timedelta(days=3)).isoformat(), "source": "Reuters India"},
            {"title": f"{mc} Q4 Preview: Revenue Growth Expected at 12-15%", "description": f"Analysts expect continuation of strong quarterly performance trend.", "url": "#", "publishedAt": (now-timedelta(days=4)).isoformat(), "source": "Bloomberg Quint"},
        ]

    # ─── Indices ──────────────────────────────────────────────
    def fetch_index_data(self) -> List[Dict]:
        """Fetch major Indian market indices - tries NSE India live API first"""
        # ── 1. Try NSE India live indices ─────────────────────
        try:
            nse = get_nse_fetcher()
            nse_indices = nse.get_indices()
            if nse_indices and len(nse_indices) >= 3:
                print(f"[DataFetcher] NSE live indices: {len(nse_indices)} fetched")
                return nse_indices
        except Exception as e:
            print(f"[DataFetcher] NSE indices failed: {e}")

        # ── 2. Try Yahoo Finance ──────────────────────────────
        from backend.config import MARKET_INDICES
        results = []
        for idx in MARKET_INDICES:
            loaded = False
            if self._yf_working:
                try:
                    stock = yf.Ticker(idx["symbol"])
                    hist = stock.history(period="5d", timeout=5)
                    if hist is not None and not hist.empty and len(hist) >= 2:
                        curr = float(hist["Close"].iloc[-1])
                        prev = float(hist["Close"].iloc[-2])
                        change = curr - prev
                        chg_pct = (change / prev * 100) if prev else 0
                        results.append({
                            "symbol": idx["symbol"],
                            "name": idx["name"],
                            "price": round(curr, 2),
                            "change": round(change, 2),
                            "change_pct": round(chg_pct, 2),
                        })
                        loaded = True
                except Exception:
                    pass

            if not loaded:
                for sym, ref in INDEX_REFERENCE.items():
                    if sym == idx["symbol"] or ref["name"] == idx["name"]:
                        rng = np.random.default_rng(int(datetime.now().strftime("%H")) + hash(sym) % 100)
                        chg_pct = float(rng.uniform(-1.2, 1.2))
                        price = ref["price"] * (1 + chg_pct / 100)
                        results.append({
                            "symbol": idx["symbol"],
                            "name": idx["name"],
                            "price": round(price, 2),
                            "change": round(price * chg_pct / 100, 2),
                            "change_pct": round(chg_pct, 2),
                        })
                        break
        return results

    # ─── Sector Heatmap ───────────────────────────────────────
    def fetch_sector_data(self) -> Dict:
        """Fetch sector heatmap data - uses NSE live prices where possible in parallel"""
        cache_key = "heatmap_data"
        if cache_key in self._cache:
            if time.time() - self._cache_ttl.get(cache_key, 0) < 180:  # Cache for 3 minutes
                return self._cache[cache_key]

        from backend.config import SECTORS
        import concurrent.futures

        nse = get_nse_fetcher()
        sector_data = {sector: [] for sector in SECTORS.keys()}

        def fetch_single(sector: str, ticker: str):
            clean = ticker.replace(".NS", "").replace(".BO", "")
            try:
                # Try NSE live price for heatmap
                live = nse.get_quote(clean)
                if live and live.get("current_price"):
                    return sector, {
                        "ticker": clean,
                        "price": live["current_price"],
                        "change_pct": live["change_pct"],
                        "market_cap": live.get("market_cap", 0),
                    }
            except Exception:
                pass

            # Fallback: use simulator with consistent seed
            try:
                rng = np.random.default_rng(int(datetime.now().strftime("%H%M")) + sum(ord(c) for c in clean))
                change_pct = float(rng.uniform(-2.5, 2.5))
                ref_data = STOCK_REFERENCE_DATA.get(clean, {"price": 500, "mc": 1e12})
                price = ref_data["price"] * (1 + change_pct / 100)
                return sector, {
                    "ticker": clean,
                    "price": round(price, 2),
                    "change_pct": round(change_pct, 2),
                    "market_cap": ref_data.get("mc", 0),
                }
            except Exception:
                return sector, None

        # Fetch in parallel with up to 15 threads to speed up the 40+ requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            future_to_stock = {}
            for sector, stocks in SECTORS.items():
                for ticker in stocks[:5]:
                    future_to_stock[executor.submit(fetch_single, sector, ticker)] = ticker

            for future in concurrent.futures.as_completed(future_to_stock):
                res = future.result()
                if res and res[1]:
                    sector_data[res[0]].append(res[1])

        self._cache[cache_key] = sector_data
        self._cache_ttl[cache_key] = time.time()
        return sector_data
