# 📈 AI-Powered Stock Market Prediction System

A production-ready, full-stack AI system for real-time stock market prediction and trading signal generation using advanced deep learning models (LSTM, Transformer) and sentiment analysis (FinBERT).

## 🌟 Features

### AI Models
- **LSTM with Attention**: 60-day lookback window, multi-feature input (OHLCV), dropout regularization
- **Transformer Time-Series**: Positional encoding, multi-head self-attention, encoder blocks
- **FinBERT Sentiment**: Financial news sentiment analysis using HuggingFace's ProsusAI/finbert

### Ensemble Strategy
- **Weighted Prediction**: 40% LSTM + 40% Transformer + 20% Sentiment-adjusted price
- **Model Agreement**: Confidence scoring based on prediction consensus

### Trading Signals
- **STRONG BUY**: Predicted > Current × 1.02 + Positive sentiment
- **BUY**: Predicted > Current
- **HOLD**: Predicted ≈ Current
- **SELL**: Predicted < Current
- **STRONG SELL**: Predicted < Current × 0.98 + Negative sentiment

### Risk Management
- Rolling volatility calculation (20-day window)
- Dynamic stop-loss suggestions
- Risk scoring (0-100)
- Confidence metrics

### Backtesting
- 1-year historical simulation
- Performance metrics: Total Return, Sharpe Ratio, Max Drawdown, Win Rate
- Trade history tracking

### Professional Dashboard
- Modern dark theme with gradient effects
- Real-time predictions and signals
- Interactive charts (Chart.js)
- Responsive design

## 📁 Project Structure

```
Stock Predictor/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # FastAPI endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   ├── lstm_model.py      # LSTM with attention
│   │   ├── transformer_model.py  # Transformer time-series
│   │   ├── ensemble_predictor.py # Ensemble logic
│   │   ├── signal_generator.py   # Trading signals
│   │   ├── risk_manager.py       # Risk analysis
│   │   ├── backtester.py         # Backtesting engine
│   │   └── saved_models/         # Trained models
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── data_fetcher.py    # yfinance + NewsAPI
│   │   ├── feature_engineering.py  # Technical indicators
│   │   └── sentiment_analyzer.py   # FinBERT integration
│   ├── config.py              # Configuration
│   └── main.py                # FastAPI app
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css      # Modern dark theme
│   │   └── js/
│   │       └── main.js        # Dashboard logic
│   └── templates/
│       └── index.html         # Main dashboard
├── train_models.py            # Model training script
├── requirements.txt           # Dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

## 🚀 Setup Instructions

### 1. Prerequisites
- Python 3.10 or higher
- pip package manager
- (Optional) NewsAPI key for real-time news

### 2. Installation

```bash
# Clone or navigate to project directory
cd "Stock Predictor"

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your NewsAPI key (optional)
# Get free key at: https://newsapi.org/
NEWSAPI_KEY=your_api_key_here
```

### 4. Train Models

Train the LSTM and Transformer models on historical data:

```bash
# Train on default stock (AAPL) with 2 years of data
python train_models.py

# Train on specific stock
python train_models.py --ticker GOOGL --period 2y

# Options:
# --ticker: Stock symbol (default: AAPL)
# --period: Historical period - 1y, 2y, 5y (default: 2y)
```

**Note**: Training may take 10-30 minutes depending on your hardware. Models will be saved to `backend/models/saved_models/`.

### 5. Run the Application

```bash
# Start the server
uvicorn backend.main:app --reload

# Or use Python directly
python -m backend.main
```

The application will be available at: **http://localhost:8000**

## 📊 Usage

### Web Dashboard

1. Open http://localhost:8000 in your browser
2. Enter a stock ticker (e.g., AAPL, GOOGL, TSLA, MSFT)
3. Click **🔮 Predict** to get AI predictions and trading signals
4. Click **📊 Backtest** to see historical performance

### API Endpoints

#### Get Prediction
```bash
curl http://localhost:8000/api/predict/AAPL
```

**Response:**
```json
{
  "ticker": "AAPL",
  "current_price": 175.50,
  "lstm_prediction": 178.20,
  "transformer_prediction": 177.80,
  "sentiment_score": 0.45,
  "final_prediction": 177.95,
  "signal": "BUY",
  "signal_color": "#90EE90",
  "reasoning": "Predicted price $177.95 is 1.40% higher than current $175.50",
  "price_change_percent": 1.40,
  "risk_score": 35.5,
  "risk_level": "MEDIUM",
  "confidence_score": 72.3,
  "confidence_level": "HIGH",
  "stop_loss": 170.25,
  "volatility": 0.023
}
```

#### Run Backtest
```bash
curl http://localhost:8000/api/backtest/AAPL
```

**Response:**
```json
{
  "ticker": "AAPL",
  "initial_capital": 10000.0,
  "final_capital": 12450.0,
  "total_return": 24.50,
  "sharpe_ratio": 1.85,
  "max_drawdown": -8.5,
  "win_rate": 65.0,
  "total_trades": 23
}
```

#### Get Stock Info
```bash
curl http://localhost:8000/api/info/AAPL
```

## 🧠 Model Architecture

### LSTM Model
- Input: (60, 5) - 60 days × 5 features (OHLCV)
- LSTM Layer 1: 128 units, return sequences
- Dropout: 0.2
- LSTM Layer 2: 64 units, return sequences
- Dropout: 0.2
- LSTM Layer 3: 32 units, return sequences
- Dropout: 0.2
- **Custom Attention Layer**
- Dense: 64 units (ReLU)
- Dense: 32 units (ReLU)
- Output: 1 unit (price prediction)

### Transformer Model
- Input: (60, 5)
- Dense Projection: 64 dimensions
- **Positional Encoding**
- **Transformer Block 1**: 4 heads, 128 FF dim
- **Transformer Block 2**: 4 heads, 128 FF dim
- **Transformer Block 3**: 4 heads, 128 FF dim
- Global Average Pooling
- Dense: 64 units (ReLU)
- Dense: 32 units (ReLU)
- Output: 1 unit

### Feature Engineering
- Technical Indicators: SMA (10, 20, 50), EMA (12, 26), MACD, RSI, Bollinger Bands
- Volatility: 20-day rolling standard deviation
- Volume indicators
- MinMax scaling (0-1)

## 📈 Performance Metrics

The system calculates:
- **Total Return**: Percentage gain/loss
- **Sharpe Ratio**: Risk-adjusted return
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Confidence Score**: Model agreement + sentiment strength + low volatility
- **Risk Score**: Volatility + model disagreement + weak sentiment

## ⚠️ Disclaimer

**IMPORTANT**: Stock market predictions are not guaranteed and should not be used as the sole basis for investment decisions. This system is designed for:
- Research purposes
- Educational demonstrations
- Algorithmic trading strategy development
- Market analysis and insights

**Always**:
- Conduct your own research
- Consult with financial advisors
- Use proper risk management
- Never invest more than you can afford to lose

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.10+
- **Deep Learning**: TensorFlow/Keras, PyTorch
- **NLP**: HuggingFace Transformers (FinBERT)
- **Data**: yfinance, NewsAPI, pandas, numpy
- **ML Tools**: scikit-learn, joblib
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **Server**: Uvicorn (ASGI)

## 🔧 Troubleshooting

### Models not found
Run `python train_models.py` to train models before making predictions.

### NewsAPI errors
The system works without NewsAPI (uses dummy sentiment). For real news, get a free key at https://newsapi.org/

### Memory issues during training
Reduce batch size in `backend/config.py`:
```python
BATCH_SIZE = 16  # Default is 32
```

### Slow predictions
First prediction loads models into memory (10-20 seconds). Subsequent predictions are faster (1-3 seconds).

## 📝 License

This project is for educational and research purposes only.

## 🤝 Contributing

Feel free to fork, modify, and enhance this system for your own use!

---

**Built with ❤️ using TensorFlow, PyTorch, FinBERT & FastAPI**
