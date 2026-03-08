"""
Portfolio manager for virtual portfolio tracking
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime


PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "portfolio_data.json")

# Vercel serverless functions only allow writing to /tmp
if os.environ.get("VERCEL") or os.environ.get("VERCEL_REGION"):
    PORTFOLIO_FILE = "/tmp/portfolio_data.json"


def _load_portfolio() -> Dict:
    """Load portfolio from JSON file"""
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(PORTFOLIO_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"holdings": [], "transactions": []}


def _save_portfolio(portfolio: Dict):
    """Save portfolio to JSON file"""
    try:
        with open(PORTFOLIO_FILE, "w") as f:
            json.dump(portfolio, f, indent=2)
    except Exception as e:
        print(f"Failed to save portfolio: {e}")


def get_portfolio() -> Dict:
    """Get portfolio with current values"""
    import yfinance as yf
    from backend.utils.data_fetcher import DataFetcher

    portfolio = _load_portfolio()
    fetcher = DataFetcher()
    holdings = portfolio.get("holdings", [])

    total_invested = 0
    total_current = 0
    enriched_holdings = []

    for h in holdings:
        try:
            current_price = fetcher.get_current_price(h["ticker"])
        except Exception:
            current_price = h.get("purchase_price", 0)

        qty = h.get("quantity", 0)
        purchase_price = h.get("purchase_price", 0)
        invested = qty * purchase_price
        current_value = qty * current_price
        pnl = current_value - invested
        pnl_pct = (pnl / invested * 100) if invested > 0 else 0

        total_invested += invested
        total_current += current_value

        enriched_holdings.append({
            **h,
            "current_price": round(current_price, 2),
            "current_value": round(current_value, 2),
            "invested": round(invested, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
        })

    total_pnl = total_current - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    return {
        "holdings": enriched_holdings,
        "total_invested": round(total_invested, 2),
        "total_current_value": round(total_current, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl_pct, 2),
        "num_holdings": len(holdings),
    }


def add_stock(ticker: str, quantity: float, purchase_price: float, date: str = None) -> Dict:
    """Add a stock to portfolio"""
    from backend.utils.data_fetcher import DataFetcher
    fetcher = DataFetcher()
    ticker = fetcher.normalize_ticker(ticker)

    portfolio = _load_portfolio()
    holdings = portfolio.get("holdings", [])

    # Check if already exists
    for h in holdings:
        if h["ticker"] == ticker:
            # Update existing holding
            total_invested = h["quantity"] * h["purchase_price"] + quantity * purchase_price
            h["quantity"] += quantity
            h["purchase_price"] = total_invested / h["quantity"]
            portfolio["holdings"] = holdings
            _save_portfolio(portfolio)
            return {"message": f"Updated {ticker} in portfolio", "ticker": ticker}

    # Add new holding
    holdings.append({
        "ticker": ticker,
        "quantity": quantity,
        "purchase_price": purchase_price,
        "date_added": date or datetime.now().strftime("%Y-%m-%d"),
    })
    portfolio["holdings"] = holdings
    _save_portfolio(portfolio)
    return {"message": f"Added {ticker} to portfolio", "ticker": ticker}


def remove_stock(ticker: str) -> Dict:
    """Remove a stock from portfolio"""
    from backend.utils.data_fetcher import DataFetcher
    fetcher = DataFetcher()
    ticker = fetcher.normalize_ticker(ticker)

    portfolio = _load_portfolio()
    holdings = portfolio.get("holdings", [])
    portfolio["holdings"] = [h for h in holdings if h["ticker"] != ticker]
    _save_portfolio(portfolio)
    return {"message": f"Removed {ticker} from portfolio"}
