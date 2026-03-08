"""
Configuration module for the Indian Stock Market Prediction System
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

# Model Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "backend" / "models" / "saved_models"
try:
    MODEL_PATH.mkdir(parents=True, exist_ok=True)
except Exception:
    pass  # Vercel serverless has a read-only filesystem

LSTM_MODEL_FILE = MODEL_PATH / "lstm_model.keras"
SCALER_FILE = MODEL_PATH / "scaler.pkl"

# Model Parameters
LOOKBACK_WINDOW = 60
BATCH_SIZE = 32
EPOCHS = 50
VALIDATION_SPLIT = 0.2

# Ensemble Weights
LSTM_WEIGHT = 0.6
SENTIMENT_WEIGHT = 0.2
TECHNICAL_WEIGHT = 0.2

# Trading Signal Thresholds
STRONG_BUY_THRESHOLD = 1.03
BUY_THRESHOLD = 1.01
SELL_THRESHOLD = 0.99
STRONG_SELL_THRESHOLD = 0.97

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))

# Indian Stock Market Config
NSE_SUFFIX = ".NS"
BSE_SUFFIX = ".BO"

# Popular Indian Stocks (NSE)
POPULAR_STOCKS = [
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "sector": "Energy"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "sector": "IT"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "sector": "Banking"},
    {"symbol": "INFY.NS", "name": "Infosys", "sector": "IT"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "sector": "Banking"},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever", "sector": "FMCG"},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "sector": "Banking"},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance", "sector": "Finance"},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel", "sector": "Telecom"},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank", "sector": "Banking"},
    {"symbol": "WIPRO.NS", "name": "Wipro", "sector": "IT"},
    {"symbol": "HCLTECH.NS", "name": "HCL Technologies", "sector": "IT"},
    {"symbol": "ASIANPAINT.NS", "name": "Asian Paints", "sector": "Consumer"},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki", "sector": "Automobile"},
    {"symbol": "TATAMOTORS.NS", "name": "Tata Motors", "sector": "Automobile"},
    {"symbol": "SUNPHARMA.NS", "name": "Sun Pharmaceutical", "sector": "Pharma"},
    {"symbol": "ITC.NS", "name": "ITC Limited", "sector": "FMCG"},
    {"symbol": "BAJAJFINSV.NS", "name": "Bajaj Finserv", "sector": "Finance"},
    {"symbol": "ONGC.NS", "name": "ONGC", "sector": "Energy"},
    {"symbol": "NTPC.NS", "name": "NTPC", "sector": "Energy"},
    {"symbol": "POWERGRID.NS", "name": "Power Grid Corp", "sector": "Energy"},
    {"symbol": "ULTRACEMCO.NS", "name": "UltraTech Cement", "sector": "Cement"},
    {"symbol": "TITAN.NS", "name": "Titan Company", "sector": "Consumer"},
    {"symbol": "TECHM.NS", "name": "Tech Mahindra", "sector": "IT"},
    {"symbol": "ADANIENT.NS", "name": "Adani Enterprises", "sector": "Conglomerate"},
]

# Major Indices
MARKET_INDICES = [
    {"symbol": "^NSEI", "name": "NIFTY 50"},
    {"symbol": "^BSESN", "name": "SENSEX"},
    {"symbol": "^NSEBANK", "name": "BANK NIFTY"},
    {"symbol": "^CNXIT", "name": "NIFTY IT"},
    {"symbol": "^CNXAUTO", "name": "NIFTY AUTO"},
    {"symbol": "^CNXPHARMA", "name": "NIFTY PHARMA"},
]

# Sector Heatmap Config
SECTORS = {
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"],
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
    "Energy": ["RELIANCE.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "COALINDIA.NS"],
    "Pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "BIOCON.NS"],
    "Automobile": ["MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS"],
    "FMCG": ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS"],
    "Finance": ["BAJFINANCE.NS", "BAJAJFINSV.NS", "HDFC.NS", "MUTHOOTFIN.NS", "CHOLAFIN.NS"],
    "Metals": ["TATASTEEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "VEDL.NS", "SAIL.NS"],
}
