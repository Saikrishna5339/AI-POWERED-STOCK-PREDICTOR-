"""
Comprehensive API routes for the Indian Stock Market Prediction Platform
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────────────────────────────────────

class PortfolioAddRequest(BaseModel):
    ticker: str
    quantity: float
    purchase_price: float
    date: Optional[str] = None


class ChatRequest(BaseModel):
    message: str


# ─────────────────────────────────────────────────────────────────────────────
# Stock Search / Autocomplete
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/search")
async def search_stocks(q: str = ""):
    """Search for Indian stocks by name or symbol"""
    from backend.config import POPULAR_STOCKS
    q = q.lower()
    if not q:
        return {"results": POPULAR_STOCKS[:10]}
    
    results = [
        s for s in POPULAR_STOCKS
        if q in s["symbol"].lower() or q in s["name"].lower() or q in s["sector"].lower()
    ]
    return {"results": results[:15]}


# ─────────────────────────────────────────────────────────────────────────────
# Market Indices
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/indices")
async def get_indices():
    """Fetch Indian market indices (NIFTY, SENSEX, BANK NIFTY, etc.)"""
    try:
        from backend.utils.data_fetcher import DataFetcher
        fetcher = DataFetcher()
        data = fetcher.fetch_index_data()
        return {"indices": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indices error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Stock Information & OHLCV
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/stock/{ticker}")
async def get_stock_info(ticker: str):
    """Get full stock information including current price, fundamentals, and metadata"""
    try:
        from backend.utils.data_fetcher import DataFetcher
        fetcher = DataFetcher()
        info = fetcher.fetch_stock_info(ticker)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stock info error: {str(e)}")


@router.get("/ohlcv/{ticker}")
async def get_ohlcv(ticker: str, period: str = "1y"):
    """Get OHLCV candlestick data for a stock"""
    try:
        from backend.utils.data_fetcher import DataFetcher
        fetcher = DataFetcher()
        data = fetcher.fetch_ohlcv(ticker, period)
        return {"ticker": ticker, "period": period, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OHLCV error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# LSTM Prediction
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/predict/{ticker}")
async def predict_stock(ticker: str):
    """
    Run LSTM prediction for a stock.
    Returns next day price, week/month trends, confidence, chart data.
    """
    try:
        from backend.models.lstm_model import StockPredictor
        predictor = StockPredictor()
        data = predictor.predict_stock(ticker)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Technical Analysis
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/technical/{ticker}")
async def get_technical_analysis(ticker: str):
    """
    Get technical indicator values and signals (RSI, MACD, Bollinger Bands, etc.)
    """
    try:
        from backend.utils.data_fetcher import DataFetcher
        from backend.utils.feature_engineering import FeatureEngineer
        
        fetcher = DataFetcher()
        engineer = FeatureEngineer()
        
        df = fetcher.fetch_stock_data(ticker, period="1y")
        ta_data = engineer.get_technical_signals(df)
        fib = engineer.fibonacci_retracement(df)
        
        return {
            "ticker": ticker,
            "technical_analysis": ta_data,
            "fibonacci": fib,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Technical analysis error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Sentiment Analysis
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/sentiment/{ticker}")
async def get_sentiment(ticker: str):
    """
    Fetch news articles and analyze sentiment for a stock
    """
    try:
        from backend.utils.data_fetcher import DataFetcher
        from backend.utils.sentiment_analyzer import SentimentAnalyzer
        
        fetcher = DataFetcher()
        analyzer = SentimentAnalyzer()
        
        news = fetcher.fetch_news(ticker, num_articles=10)
        sentiment = analyzer.analyze_news_batch(news)
        
        # Add per-article sentiment
        articles_with_sentiment = []
        for article in news[:8]:
            text = f"{article.get('title', '')} {article.get('description', '')}"
            article_sentiment = analyzer.analyze_text(text)
            articles_with_sentiment.append({
                **article,
                "sentiment": article_sentiment.get("sentiment_score", 0),
                "sentiment_label": (
                    "Positive" if article_sentiment.get("sentiment_score", 0) > 0.1
                    else "Negative" if article_sentiment.get("sentiment_score", 0) < -0.1
                    else "Neutral"
                ),
            })
        
        return {
            "ticker": ticker,
            "overall_sentiment": sentiment,
            "articles": articles_with_sentiment,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# AI Recommendation
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/recommendation/{ticker}")
async def get_recommendation(ticker: str):
    """
    Generate AI-powered BUY/SELL/HOLD recommendation combining
    prediction, technical analysis, and sentiment
    """
    try:
        from backend.models.lstm_model import StockPredictor
        from backend.models.risk_manager import RiskManager
        
        predictor = StockPredictor()
        risk_mgr = RiskManager()
        
        pred_data = predictor.predict_stock(ticker)
        risk_data = risk_mgr.calculate_all_metrics(ticker)
        recommendation = predictor.generate_ai_recommendation(pred_data, risk_data)
        
        return {
            "ticker": ticker,
            "recommendation": recommendation,
            "prediction_summary": {
                "current_price": pred_data["current_price"],
                "next_day_price": pred_data["next_day_price"],
                "price_change_pct": pred_data["price_change_pct"],
                "confidence_score": pred_data["confidence_score"],
            },
            "risk_summary": {
                "risk_level": risk_data["risk_level"],
                "risk_score": risk_data["risk_score"],
                "volatility": risk_data["volatility"],
            },
            "technical_summary": pred_data.get("technical_analysis", {}).get("overall_signal", "HOLD"),
            "sentiment_summary": pred_data.get("sentiment_data", {}).get("sentiment_label", "Neutral"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Risk Analysis
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/risk/{ticker}")
async def get_risk_analysis(ticker: str):
    """
    Get comprehensive risk metrics: volatility, Sharpe, Beta, Max Drawdown, VaR
    """
    try:
        from backend.models.risk_manager import RiskManager
        rm = RiskManager()
        data = rm.calculate_all_metrics(ticker)
        return {"ticker": ticker, **data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Backtesting
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/backtest/{ticker}")
async def backtest_stock(ticker: str, strategy: str = "sma", capital: float = 100000):
    """
    Run backtesting for a stock with specified strategy.
    Strategies: sma, rsi, macd, buyhold
    """
    try:
        from backend.models.backtester import Backtester
        bt = Backtester()
        # Run all strategies for comparison
        all_results = bt.run_all_strategies(ticker, capital)
        single_result = bt.run_backtest(ticker, strategy, capital)
        return {
            "ticker": ticker,
            "strategy": strategy,
            "result": single_result,
            "all_strategies": all_results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Sector Heatmap
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/heatmap")
async def get_heatmap():
    """Get sector heatmap data showing gainers (green) and losers (red)"""
    try:
        from backend.utils.data_fetcher import DataFetcher
        fetcher = DataFetcher()
        data = fetcher.fetch_sector_data()
        return {"heatmap": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Heatmap error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Portfolio Management
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/portfolio")
async def get_portfolio():
    """Get current portfolio with live prices and P&L"""
    try:
        from backend.models.portfolio_manager import get_portfolio as gp
        return gp()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio error: {str(e)}")


@router.post("/portfolio/add")
async def add_to_portfolio(request: PortfolioAddRequest):
    """Add a stock to the virtual portfolio"""
    try:
        from backend.models.portfolio_manager import add_stock
        result = add_stock(request.ticker, request.quantity, request.purchase_price, request.date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio add error: {str(e)}")


@router.delete("/portfolio/{ticker}")
async def remove_from_portfolio(ticker: str):
    """Remove a stock from the portfolio"""
    try:
        from backend.models.portfolio_manager import remove_stock
        result = remove_stock(ticker)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio remove error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# AI Chat Assistant
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(request: ChatRequest):
    """AI chat assistant for stock market queries"""
    try:
        from backend.models.chat_assistant import ChatAssistant
        assistant = ChatAssistant()
        response = assistant.process_message(request.message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Historical Price Chart
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/history/{ticker}")
async def get_price_history(ticker: str, period: str = "1y"):
    """Get price history for line chart"""
    try:
        from backend.utils.data_fetcher import DataFetcher
        fetcher = DataFetcher()
        df = fetcher.fetch_stock_data(ticker, period)
        data = []
        for _, row in df.iterrows():
            data.append({
                "date": str(row["Date"])[:10],
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })
        return {"ticker": ticker, "period": period, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Popular Stocks List
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/popular-stocks")
async def get_popular_stocks():
    """Get list of popular Indian stocks"""
    from backend.config import POPULAR_STOCKS
    return {"stocks": POPULAR_STOCKS}
