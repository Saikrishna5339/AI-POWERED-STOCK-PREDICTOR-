"""
Optimized Stock Prediction Engine for Indian Market
Uses sklearn Linear Regression + feature engineering for fast, reliable predictions.
Optionally upgrades to LSTM if TensorFlow is available.
"""
import numpy as np
import pandas as pd
from typing import Dict, List
import warnings
warnings.filterwarnings("ignore")


class StockPredictor:
    """Fast stock price predictor using Linear Regression (or LSTM if TF available)"""

    def predict_stock(self, ticker: str) -> Dict:
        """
        Main prediction pipeline.
        Returns next-day price, week/month trends, confidence, chart data.
        """
        from backend.utils.data_fetcher import DataFetcher
        from backend.utils.feature_engineering import FeatureEngineer
        from backend.utils.sentiment_analyzer import SentimentAnalyzer

        fetcher = DataFetcher()
        engineer = FeatureEngineer()
        sentiment_analyzer = SentimentAnalyzer()

        # Fetch 1y of data (fast with simulator)
        df = fetcher.fetch_stock_data(ticker, period="1y")
        if df.empty or len(df) < 30:
            raise ValueError(f"Insufficient data for {ticker}")

        current_price = float(df["Close"].iloc[-1])

        # ── Feature Engineering ──────────────────────────────────
        try:
            features_df = engineer.compute_technical_indicators(df)
            if features_df is not None and not features_df.empty:
                features_df = features_df.dropna()
            else:
                features_df = df.copy()
        except Exception:
            features_df = df.copy()
        if len(features_df) < 20:
            features_df = df.copy()

        # ── Technical Analysis ────────────────────────────────────
        ta_data = {}
        fib_data = {}
        try:
            ta_data = engineer.get_technical_signals(df)
            fib_data = engineer.fibonacci_retracement(df)
        except Exception:
            pass

        # ── Sentiment Analysis ────────────────────────────────────
        sentiment_data = {"sentiment_score": 0, "sentiment_label": "Neutral"}
        news_articles = []
        try:
            news_articles = fetcher.fetch_news(ticker, num_articles=7)
            sentiment_data = sentiment_analyzer.analyze_news_batch(news_articles)
        except Exception:
            pass

        # ── Price Prediction ──────────────────────────────────────
        next_day, week_trend, month_trend, rmse, mae, mape, model_name, actual_arr, pred_arr = \
            self._run_prediction(df, features_df, current_price)

        price_change_pct = ((next_day - current_price) / current_price * 100) if current_price else 0

        # ── Confidence Score ──────────────────────────────────────
        confidence = self._compute_confidence(
            price_change_pct, ta_data, sentiment_data, mape
        )

        # ── Chart Data ────────────────────────────────────────────
        n_chart = min(60, len(actual_arr))
        chart_dates = []
        if "Date" in df.columns:
            chart_dates = [str(d)[:10] for d in df["Date"].iloc[-n_chart:].tolist()]

        return {
            "ticker": ticker,
            "current_price": round(current_price, 2),
            "next_day_price": round(next_day, 2),
            "next_week_trend": round(week_trend, 2),
            "next_month_trend": round(month_trend, 2),
            "price_change_pct": round(price_change_pct, 2),
            "rmse": round(rmse, 2),
            "mae": round(mae, 2),
            "mape": round(mape, 2),
            "confidence_score": round(confidence, 1),
            "model_used": model_name,
            "chart_actual": [round(float(v), 2) for v in actual_arr[-n_chart:]],
            "chart_predicted": [round(float(v), 2) for v in pred_arr[-n_chart:]],
            "chart_dates": chart_dates,
            "technical_analysis": ta_data,
            "sentiment_data": sentiment_data,
            "news_articles": news_articles[:5],
        }

    def _run_prediction(self, df: pd.DataFrame, features_df: pd.DataFrame, current_price: float):
        """Run the prediction model - sklearn with optional TF/LSTM upgrade"""
        closes = df["Close"].values.astype(float)
        n = len(closes)

        # First try LSTM if TensorFlow is available
        try:
            result = self._lstm_predict(closes)
            if result is not None:
                return result
        except Exception:
            pass

        # Fallback: sklearn Linear Regression
        return self._linear_predict(closes, current_price)

    def _linear_predict(self, closes: np.ndarray, current_price: float):
        """Fast linear regression prediction using momentum features"""
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import mean_squared_error, mean_absolute_error

        n = len(closes)
        lookback = min(20, n // 3)

        # Build features: lag returns, MA ratios
        X, y = [], []
        for i in range(lookback, n):
            window = closes[i - lookback:i]
            feat = [
                (closes[i-1] - closes[i-2]) / closes[i-2] if closes[i-2] > 0 else 0,
                (closes[i-1] - closes[i-5]) / closes[i-5] if i >= 5 and closes[i-5] > 0 else 0,
                (closes[i-1] - closes[i-10]) / closes[i-10] if i >= 10 and closes[i-10] > 0 else 0,
                np.mean(window) / closes[i-1] if closes[i-1] > 0 else 1,
                np.std(window) / closes[i-1] if closes[i-1] > 0 else 0,
                float(i) / n,  # time trend
            ]
            X.append(feat)
            y.append(closes[i])

        X, y = np.array(X), np.array(y)

        split = int(len(X) * 0.8)
        X_train, X_val = X[:split], X[split:]
        y_train, y_val = y[:split], y[split:]

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_val_s = scaler.transform(X_val)

        model = Ridge(alpha=1.0)
        model.fit(X_train_s, y_train)

        # Predictions for chart (full history)
        all_X_s = scaler.transform(X)
        all_pred = model.predict(all_X_s)

        # Actual vs predicted arrays
        actual_arr = closes[lookback:]
        pred_arr = all_pred

        # Metrics (on validation set)
        val_pred = model.predict(X_val_s)
        rmse = float(np.sqrt(mean_squared_error(y_val, val_pred)))
        mae = float(mean_absolute_error(y_val, val_pred))
        mape = float(np.mean(np.abs((y_val - val_pred) / y_val)) * 100) if np.all(y_val != 0) else 5.0

        # Next day prediction
        last_window = closes[-lookback:]
        next_feat = [
            (closes[-1] - closes[-2]) / closes[-2] if closes[-2] > 0 else 0,
            (closes[-1] - closes[-5]) / closes[-5] if len(closes) >= 5 and closes[-5] > 0 else 0,
            (closes[-1] - closes[-10]) / closes[-10] if len(closes) >= 10 and closes[-10] > 0 else 0,
            np.mean(last_window) / closes[-1] if closes[-1] > 0 else 1,
            np.std(last_window) / closes[-1] if closes[-1] > 0 else 0,
            1.0,  # time = end
        ]
        next_day = float(model.predict(scaler.transform([next_feat]))[0])

        # Week and month trends (extrapolate with decay)
        daily_drift = (next_day - current_price) / current_price
        week_trend = current_price * (1 + daily_drift * 5 * 0.7)
        month_trend = current_price * (1 + daily_drift * 20 * 0.5)

        return next_day, week_trend, month_trend, rmse, mae, mape, "Linear Regression (Fallback)", actual_arr, pred_arr

    def _lstm_predict(self, closes: np.ndarray):
        """Try LSTM prediction with TensorFlow"""
        try:
            import tensorflow as tf
            from tensorflow import keras
            from sklearn.preprocessing import MinMaxScaler
            from sklearn.metrics import mean_squared_error, mean_absolute_error

            lookback = 30
            if len(closes) < lookback * 2:
                return None

            scaler = MinMaxScaler()
            scaled = scaler.fit_transform(closes.reshape(-1, 1))

            X, y = [], []
            for i in range(lookback, len(scaled)):
                X.append(scaled[i - lookback:i, 0])
                y.append(scaled[i, 0])
            X, y = np.array(X), np.array(y)
            X = X.reshape(X.shape[0], X.shape[1], 1)

            split = int(len(X) * 0.8)
            X_train, X_val = X[:split], X[split:]
            y_train, y_val = y[:split], y[split:]

            model = keras.Sequential([
                keras.layers.LSTM(64, return_sequences=True, input_shape=(lookback, 1)),
                keras.layers.Dropout(0.2),
                keras.layers.LSTM(32),
                keras.layers.Dropout(0.2),
                keras.layers.Dense(1),
            ])
            model.compile(optimizer="adam", loss="mse")
            model.fit(X_train, y_train, epochs=20, batch_size=16,
                      validation_data=(X_val, y_val), verbose=0,
                      callbacks=[keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)])

            # Next day
            last_seq = scaled[-lookback:].reshape(1, lookback, 1)
            next_scaled = float(model.predict(last_seq, verbose=0)[0][0])
            next_day = float(scaler.inverse_transform([[next_scaled]])[0][0])

            # Full prediction for chart
            all_pred_s = model.predict(X, verbose=0).flatten()
            pred_arr = scaler.inverse_transform(all_pred_s.reshape(-1, 1)).flatten()
            actual_arr = closes[lookback:]

            val_pred_s = model.predict(X_val, verbose=0).flatten()
            val_pred = scaler.inverse_transform(val_pred_s.reshape(-1, 1)).flatten()
            y_val_inv = scaler.inverse_transform(y_val.reshape(-1, 1)).flatten()

            rmse = float(np.sqrt(mean_squared_error(y_val_inv, val_pred)))
            mae = float(mean_absolute_error(y_val_inv, val_pred))
            mape = float(np.mean(np.abs((y_val_inv - val_pred) / y_val_inv)) * 100) if np.all(y_val_inv != 0) else 5.0

            current = float(closes[-1])
            daily_drift = (next_day - current) / current
            week_trend = current * (1 + daily_drift * 5 * 0.7)
            month_trend = current * (1 + daily_drift * 20 * 0.5)

            return next_day, week_trend, month_trend, rmse, mae, mape, "LSTM Neural Network", actual_arr, pred_arr
        except ImportError:
            print("[WARN] TensorFlow not available, falling back to statistical")
            return None
        except Exception as e:
            print(f"LSTM prediction error: {e}")
            return None

    def _compute_confidence(self, price_change_pct: float, ta_data: Dict,
                            sentiment_data: Dict, mape: float) -> float:
        """Compute overall confidence score 0-100"""
        score = 50.0  # Base

        # Technical signal contribution
        ta_signal = ta_data.get("overall_signal", "HOLD")
        predicted_up = price_change_pct >= 0
        if (predicted_up and "BUY" in ta_signal) or (not predicted_up and "SELL" in ta_signal):
            score += 15
        elif ta_signal == "HOLD":
            score += 5

        # Sentiment contribution
        sent_score = sentiment_data.get("sentiment_score", 0)
        if (predicted_up and sent_score > 0.1) or (not predicted_up and sent_score < -0.1):
            score += 10
        elif abs(sent_score) < 0.05:
            score += 3

        # Error-based penalty
        score -= min(20, mape * 0.5)

        # Limit prediction range
        if abs(price_change_pct) > 10:
            score -= 15  # Extreme predictions are less confident

        return max(10.0, min(95.0, score))

    def generate_ai_recommendation(self, pred_data: Dict, risk_data: Dict) -> Dict:
        """Generate BUY/SELL/HOLD recommendation with reasoning"""
        score = 0
        reasons = []

        # Price momentum
        pct = pred_data.get("price_change_pct", 0)
        if pct > 2:
            score += 30
            reasons.append(f"Bullish price prediction (+{pct:.1f}%)")
        elif pct > 0.5:
            score += 15
            reasons.append(f"Modest upside predicted (+{pct:.1f}%)")
        elif pct < -2:
            score -= 30
            reasons.append(f"Bearish price prediction ({pct:.1f}%)")
        elif pct < -0.5:
            score -= 15
            reasons.append(f"Slight downside predicted ({pct:.1f}%)")

        # Technical analysis
        ta = pred_data.get("technical_analysis", {})
        ta_signal = ta.get("overall_signal", "HOLD")
        if "STRONG BUY" in ta_signal:
            score += 25
            reasons.append("Strong technical buy signals")
        elif "BUY" in ta_signal:
            score += 15
            reasons.append("Positive technical indicators")
        elif "STRONG SELL" in ta_signal:
            score -= 25
            reasons.append("Strong technical sell signals")
        elif "SELL" in ta_signal:
            score -= 15
            reasons.append("Negative technical indicators")

        # Sentiment
        sent = pred_data.get("sentiment_data", {})
        sent_score = sent.get("sentiment_score", 0)
        if sent_score > 0.2:
            score += 15
            reasons.append("Strongly positive news sentiment")
        elif sent_score > 0.05:
            score += 8
            reasons.append("Positive news sentiment")
        elif sent_score < -0.2:
            score -= 15
            reasons.append("Negative news sentiment")
        elif sent_score < -0.05:
            score -= 8
            reasons.append("Slightly negative sentiment")

        # Risk adjustment
        risk_level = risk_data.get("risk_level", "Medium Risk")
        sharpe = risk_data.get("sharpe_ratio", 0)
        if sharpe > 1.0:
            score += 10
            reasons.append(f"Good Sharpe ratio ({sharpe:.2f})")
        elif sharpe < 0:
            score -= 10
            reasons.append("Poor risk-adjusted returns")
        if "High Risk" in risk_level:
            score -= 5
            reasons.append("High volatility warning")

        # Generate signal
        if score >= 35:
            sig, color = "STRONG BUY", "#00b894"
        elif score >= 15:
            sig, color = "BUY", "#10b981"
        elif score <= -35:
            sig, color = "STRONG SELL", "#d63031"
        elif score <= -15:
            sig, color = "SELL", "#ef4444"
        else:
            sig, color = "HOLD", "#f59e0b"

        confidence = min(95, max(30, 50 + abs(score)))

        return {
            "recommendation": sig,
            "color": color,
            "confidence": round(confidence, 1),
            "score": round(score, 1),
            "reasons": reasons[:5],
            "summary": f"Based on LSTM prediction, technical analysis, and market sentiment, the AI recommends: {sig}",
        }


# Keep backward compatibility
class LSTMPredictor(StockPredictor):
    """Alias for legacy code"""
    pass
