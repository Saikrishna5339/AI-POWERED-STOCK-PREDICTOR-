"""
Simplified FastAPI application - runs without AI models
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from pydantic import BaseModel
import yfinance as yf

# Create FastAPI app
app = FastAPI(
    title="AI Stock Market Prediction System",
    description="Real-time stock market prediction (Simplified Demo Mode)",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent.parent / "frontend" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Serve frontend
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main dashboard"""
    template_path = Path(__file__).parent.parent / "frontend" / "templates" / "index.html"
    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h1>Stock Prediction System</h1><p>Frontend not found</p>"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Stock Prediction API is running (Demo Mode)"}

# Simplified prediction endpoint
@app.get("/api/predict/{ticker}")
async def predict_stock(ticker: str):
    """
    Get stock prediction (simplified demo version)
    """
    try:
        ticker = ticker.upper()
        
        # Fetch current stock data
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No data found for ticker {ticker}")
        
        current_price = float(hist['Close'].iloc[-1])
        
        # Simple prediction based on recent trend
        if len(hist) >= 2:
            prev_price = float(hist['Close'].iloc[-2])
            trend = (current_price - prev_price) / prev_price
        else:
            trend = 0
        
        # Generate simple predictions
        lstm_prediction = current_price * (1 + trend * 0.8)
        transformer_prediction = current_price * (1 + trend * 0.9)
        sentiment_score = trend * 2  # Simple sentiment proxy
        final_prediction = current_price * (1 + trend)
        
        # Generate signal
        if final_prediction > current_price * 1.02:
            signal = "STRONG BUY"
            color = "#00ff00"
        elif final_prediction > current_price:
            signal = "BUY"
            color = "#90EE90"
        elif final_prediction < current_price * 0.98:
            signal = "STRONG SELL"
            color = "#ff0000"
        elif final_prediction < current_price:
            signal = "SELL"
            color = "#FFB6C1"
        else:
            signal = "HOLD"
            color = "#FFD700"
        
        price_change = ((final_prediction - current_price) / current_price) * 100
        
        return {
            "ticker": ticker,
            "current_price": current_price,
            "lstm_prediction": lstm_prediction,
            "transformer_prediction": transformer_prediction,
            "sentiment_score": sentiment_score,
            "final_prediction": final_prediction,
            "signal": signal,
            "signal_color": color,
            "reasoning": f"Demo mode: Predicted price ${final_prediction:.2f} vs current ${current_price:.2f}",
            "price_change_percent": price_change,
            "risk_score": 50.0,
            "risk_level": "MEDIUM",
            "confidence_score": 60.0,
            "confidence_level": "MEDIUM",
            "stop_loss": current_price * 0.95,
            "volatility": 0.02
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.get("/api/backtest/{ticker}")
async def backtest_stock(ticker: str):
    """
    Run backtest (simplified demo version)
    """
    return {
        "ticker": ticker.upper(),
        "initial_capital": 10000.0,
        "final_capital": 11500.0,
        "total_return": 15.0,
        "sharpe_ratio": 1.2,
        "max_drawdown": -5.5,
        "win_rate": 60.0,
        "total_trades": 15
    }

@app.get("/api/info/{ticker}")
async def get_stock_info(ticker: str):
    """Get basic stock information"""
    try:
        ticker = ticker.upper()
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return {
            'ticker': ticker,
            'name': info.get('longName', ticker),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Info error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main_simple:app", host="0.0.0.0", port=8000, reload=True)
