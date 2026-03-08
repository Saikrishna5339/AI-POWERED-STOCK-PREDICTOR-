# AI-Powered Stock Predictor: Technical Project Details

This document outlines the architecture, features, machine learning models, and the technology stack driving the **AI-Powered Stock Predictor** designed for the Indian Markets (NSE/BSE).

---

## 🚀 Core Features & Their Purpose

1. **Intelligent Market Dashboard**
   - **Feature:** A central hub showing real-time price quotes, percentage changes, gap-up/gap-down indicators, and market capitalization.
   - **Purpose:** Gives traders an immediate, at-a-glance macroeconomic view of a specific stock before they dive into deeper predictive analysis.

2. **Advanced Candlestick Charting (TradingView Style)**
   - **Feature:** Interactive OHLCV (Open, High, Low, Close, Volume) candlestick charts powered by `lightweight-charts`.
   - **Purpose:** Essential for visual pattern recognition, drawing trendlines, and understanding the momentum of the market over customizable timeframes (3M, 6M, 1Y, etc.).

3. **Machine Learning Price Prediction (LSTM Engine)**
   - **Feature:** Forecasts upcoming stock price movements with a confidence score and generates "Bullish" or "Bearish" signals. Displays actual vs. predicted price plots.
   - **Purpose:** To provide algorithm-backed future price direction using historical trends, moving away from purely speculative trading.

4. **Technical Analysis (TA) Modules**
   - **Feature:** Computes industry-standard indicators including RSI (Relative Strength Index), MACD (Moving Average Convergence Divergence), Bollinger Bands, and Exponential Moving Averages (EMA).
   - **Purpose:** Identifies overbought or oversold conditions and potential trend reversals, forming the mathematical backbone of short-term trading signals.

5. **News Sentiment Analysis**
   - **Feature:** Scrapes real-time financial news headlines related to the queried ticker and scores them using Natural Language Processing (NLP).
   - **Purpose:** Stock prices are heavily influenced by human psychology and news. Sentiment scores (Positive, Neutral, Negative) provide a qualitative layer to the quantitative LSTM predictions.

6. **Algorithmic Backtesting Simulator**
   - **Feature:** Allows users to simulate historical trading strategies (e.g., MACD Crossover, RSI Reversal) against the stock's past performance to see hypothetical P&L.
   - **Purpose:** "Never trade a strategy you haven't tested." This feature proves whether the mathematical indicators actually generated profit on this specific stock over the last year.

7. **Risk Metrics & Volatility Dashboard**
   - **Feature:** Calculates Maximum Drawdown, Value at Risk (VaR), Annualized Volatility, and the Sharpe Ratio.
   - **Purpose:** Protects the trader. High returns mean nothing if the risk of ruin is too high. This module quantifies exactly how dangerous a stock is to hold.

8. **AI Chat Assistant**
   - **Feature:** A conversational interface where users can ask questions directly about a stock's technicals or prediction.
   - **Purpose:** Translates complex mathematical data (like MACD histograms or RSI levels) into plain English for newer or retail investors.

---

## 🧠 The Machine Learning Model: Why LSTM?

The predictive core of this application relies on a **Long Short-Term Memory (LSTM)** neural network.

### What is LSTM?
LSTM is a type of Recurrent Neural Network (RNN) architecture explicitly designed to handle sequential, time-series data. Unlike traditional neural networks that treat inputs independently, LSTMs have "memory cells" that can maintain information in memory for long periods of time. 

### Why Use LSTM for Stock Prices?
Stock prices are the ultimate time-series problem. Today's price is highly dependent on yesterday's price, the price 10 days ago, and broader historical patterns. 
- **The Vanishing Gradient Problem:** Standard RNNs "forget" older data when looking at long sequences (e.g., 200 days of stock data). LSTMs use special "gates" (Forget, Input, Output) to decide what past information to keep and what to throw away, perfectly preserving long-term trends.
- **Pattern Recognition:** LSTMs are exceptionally good at finding non-linear patterns (like head-and-shoulders, or cyclical earnings crashes) that traditional statistical models (like ARIMA) miss.

### Model Architecture & Training Process in This Project
1. **Feature Engineering:** We don't just feed the model the raw `Close` price. The AI is trained on engineered features: 
   - Price Rates of Change
   - Moving Averages (SMA 20, SMA 50)
   - RSI and MACD values
   - Historical Volatility
2. **Data Scaling:** Neural networks struggle with wild numerical ranges. We use `MinMaxScaler` to compress all stock prices and indicator values between `0` and `1`.
3. **Windowing (Lookback):** We organize the data into "windows." For example, the model looks at the previous **60 sequential trading days** of data to predict the outcome of **Day 61**. 
4. **Architecture Layers:** 
   - **Input Layer:** Takes the 3D windowed data.
   - **LSTM Layers:** Extracts the temporal patterns.
   - **Dropout Layers:** Randomly turns off neurons during training to prevent the model from "memorizing" the exact past (preventing overfitting).
   - **Dense Output Layer:** Compresses the network's understanding into a single predicted continuous value (the price).

---

## 🛠️ Technology Stack

### Backend (The Brain)
*   **Python 3:** The industry-standard language for machine learning and quantitative finance.
*   **Flask / FastAPI:** Serves as the web framework delivering blazing-fast API endpoints.
*   **TensorFlow / Keras:** The deep learning framework used to construct and train the LSTM neural networks.
*   **Pandas & NumPy:** For high-performance vector math, array manipulation, and financial DataFrame transformations.
*   **Scikit-Learn:** Used for data preprocessing (MinMaxScaler) and evaluation metrics (RMSE, MAE).
*   **NLTK / VADER:** The Natural Language Processing toolkit used to parse and score the sentiment of financial news articles.

### Frontend (The Face)
*   **Vanilla HTML5 / CSS3 / JavaScript:** Built without heavy frameworks (like React) to keep the initial load time virtually instantaneous.
*   **Flexbox & CSS Grid:** For a liquid, fully responsive UI that meticulously adapts from 4K desktop monitors down to 320px mobile screens.
*   **TradingView Lightweight Charts:** An ultra-fast HTML5 Canvas library specifically built for financial charting. Handles thousands of candlesticks without browser lag.
*   **Chart.js:** Used for rendering the smooth gradient line charts (Actual vs. Predicted) and the doughnut charts (RSI Gauge).

### Data & Deployment
*   **NSE/BSE Real-Time APIs:** Bypasses rate-limited generic APIs to pull highly accurate, localized data for Indian markets.
*   **Vercel:** A serverless deployment platform. Allows the Python backend to spin up instantly on-demand ("Serverless Functions") while distributing the frontend assets via a global Edge Network (CDN).
