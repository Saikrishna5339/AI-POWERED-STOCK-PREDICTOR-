"""
Technical analysis feature engineering for Indian stocks
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class FeatureEngineer:
    """Computes technical indicators and prepares features for ML models"""

    def compute_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute all technical indicators

        Args:
            df: DataFrame with OHLCV columns

        Returns:
            DataFrame with added indicator columns
        """
        df = df.copy()

        # --- Moving Averages ---
        df["SMA_20"] = df["Close"].rolling(window=20).mean()
        df["SMA_50"] = df["Close"].rolling(window=50).mean()
        df["SMA_200"] = df["Close"].rolling(window=200).mean()
        df["EMA_12"] = df["Close"].ewm(span=12, adjust=False).mean()
        df["EMA_26"] = df["Close"].ewm(span=26, adjust=False).mean()
        df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()

        # --- MACD ---
        df["MACD"] = df["EMA_12"] - df["EMA_26"]
        df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

        # --- RSI ---
        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, 1e-10)
        df["RSI"] = 100 - (100 / (1 + rs))

        # --- Bollinger Bands ---
        rolling_mean = df["Close"].rolling(window=20).mean()
        rolling_std = df["Close"].rolling(window=20).std()
        df["BB_Upper"] = rolling_mean + (rolling_std * 2)
        df["BB_Lower"] = rolling_mean - (rolling_std * 2)
        df["BB_Middle"] = rolling_mean
        df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / df["BB_Middle"]
        df["BB_Position"] = (df["Close"] - df["BB_Lower"]) / (
            df["BB_Upper"] - df["BB_Lower"] + 1e-10
        )

        # --- Stochastic Oscillator ---
        low_14 = df["Low"].rolling(window=14).min()
        high_14 = df["High"].rolling(window=14).max()
        df["Stoch_K"] = 100 * (df["Close"] - low_14) / (high_14 - low_14 + 1e-10)
        df["Stoch_D"] = df["Stoch_K"].rolling(window=3).mean()

        # --- Average True Range (ATR) ---
        hl = df["High"] - df["Low"]
        hc = (df["High"] - df["Close"].shift()).abs()
        lc = (df["Low"] - df["Close"].shift()).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        df["ATR"] = tr.rolling(window=14).mean()

        # --- Volume Indicators ---
        df["Volume_SMA"] = df["Volume"].rolling(window=20).mean()
        df["Volume_Ratio"] = df["Volume"] / (df["Volume_SMA"] + 1e-10)
        df["OBV"] = (np.sign(df["Close"].diff()) * df["Volume"]).fillna(0).cumsum()

        # --- Price Change Features ---
        df["Returns"] = df["Close"].pct_change()
        df["Log_Returns"] = np.log(df["Close"] / df["Close"].shift(1))
        df["Volatility_20"] = df["Returns"].rolling(window=20).std()

        # --- Momentum Indicators ---
        df["ROC_10"] = df["Close"].pct_change(periods=10) * 100
        df["ROC_20"] = df["Close"].pct_change(periods=20) * 100

        # --- Price Position ---
        df["High_Low_Pct"] = (df["High"] - df["Low"]) / df["Close"]
        df["Open_Close_Pct"] = (df["Close"] - df["Open"]) / df["Open"]

        return df

    def get_feature_columns(self) -> List[str]:
        """Return the feature columns used for ML training"""
        return [
            "Close", "Volume", "SMA_20", "SMA_50", "EMA_12", "EMA_26",
            "MACD", "MACD_Signal", "RSI", "BB_Upper", "BB_Lower",
            "BB_Width", "BB_Position", "ATR", "Volume_Ratio",
            "Returns", "Volatility_20", "ROC_10", "Stoch_K", "OBV",
        ]

    def prepare_lstm_sequences(
        self, df: pd.DataFrame, lookback: int = 60
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare input sequences for LSTM model

        Returns:
            X (sequences), y (targets)
        """
        df = self.compute_technical_indicators(df)
        features = self.get_feature_columns()

        # Drop na rows
        df = df.dropna()

        feature_data = df[features].values
        target_data = df["Close"].values

        X, y = [], []
        for i in range(lookback, len(feature_data)):
            X.append(feature_data[i - lookback : i])
            y.append(target_data[i])

        return np.array(X), np.array(y)

    def get_technical_signals(self, df: pd.DataFrame) -> Dict:
        """
        Generate BUY/SELL/HOLD signals from technical indicators

        Returns:
            Dict with signal for each indicator and overall signal
        """
        df = self.compute_technical_indicators(df)
        latest = df.iloc[-1]

        signals = {}
        scores = []

        # --- RSI Signal ---
        rsi = latest.get("RSI", 50)
        if rsi < 30:
            signals["RSI"] = {"signal": "BUY", "value": round(rsi, 2), "reason": "Oversold (<30)"}
            scores.append(1)
        elif rsi > 70:
            signals["RSI"] = {"signal": "SELL", "value": round(rsi, 2), "reason": "Overbought (>70)"}
            scores.append(-1)
        else:
            signals["RSI"] = {"signal": "HOLD", "value": round(rsi, 2), "reason": "Neutral (30-70)"}
            scores.append(0)

        # --- MACD Signal ---
        macd = latest.get("MACD", 0)
        macd_signal = latest.get("MACD_Signal", 0)
        macd_hist = latest.get("MACD_Hist", 0)
        if macd > macd_signal and macd_hist > 0:
            signals["MACD"] = {"signal": "BUY", "value": round(macd, 4), "reason": "Bullish crossover"}
            scores.append(1)
        elif macd < macd_signal and macd_hist < 0:
            signals["MACD"] = {"signal": "SELL", "value": round(macd, 4), "reason": "Bearish crossover"}
            scores.append(-1)
        else:
            signals["MACD"] = {"signal": "HOLD", "value": round(macd, 4), "reason": "No clear crossover"}
            scores.append(0)

        # --- Moving Average Signal ---
        close = latest.get("Close", 0)
        sma_20 = latest.get("SMA_20", 0)
        sma_50 = latest.get("SMA_50", 0)
        sma_200 = latest.get("SMA_200", 0)
        if close > sma_20 > sma_50:
            signals["Moving_Average"] = {"signal": "BUY", "value": round(close, 2), "reason": "Price > SMA20 > SMA50"}
            scores.append(1)
        elif close < sma_20 < sma_50:
            signals["Moving_Average"] = {"signal": "SELL", "value": round(close, 2), "reason": "Price < SMA20 < SMA50"}
            scores.append(-1)
        else:
            signals["Moving_Average"] = {"signal": "HOLD", "value": round(close, 2), "reason": "Mixed MA signals"}
            scores.append(0)

        # --- Bollinger Bands Signal ---
        bb_pos = latest.get("BB_Position", 0.5)
        if bb_pos < 0.1:
            signals["Bollinger_Bands"] = {"signal": "BUY", "value": round(bb_pos, 3), "reason": "Near lower band (oversold)"}
            scores.append(1)
        elif bb_pos > 0.9:
            signals["Bollinger_Bands"] = {"signal": "SELL", "value": round(bb_pos, 3), "reason": "Near upper band (overbought)"}
            scores.append(-1)
        else:
            signals["Bollinger_Bands"] = {"signal": "HOLD", "value": round(bb_pos, 3), "reason": "Within bands"}
            scores.append(0)

        # --- Volume Signal ---
        vol_ratio = latest.get("Volume_Ratio", 1.0)
        if vol_ratio > 1.5:
            signals["Volume"] = {"signal": "STRONG", "value": round(vol_ratio, 2), "reason": "High volume (1.5x avg)"}
        else:
            signals["Volume"] = {"signal": "NORMAL", "value": round(vol_ratio, 2), "reason": "Normal volume"}

        # --- Stochastic Signal ---
        stoch_k = latest.get("Stoch_K", 50)
        stoch_d = latest.get("Stoch_D", 50)
        if stoch_k < 20 and stoch_d < 20:
            signals["Stochastic"] = {"signal": "BUY", "value": round(stoch_k, 2), "reason": "Oversold (<20)"}
            scores.append(1)
        elif stoch_k > 80 and stoch_d > 80:
            signals["Stochastic"] = {"signal": "SELL", "value": round(stoch_k, 2), "reason": "Overbought (>80)"}
            scores.append(-1)
        else:
            signals["Stochastic"] = {"signal": "HOLD", "value": round(stoch_k, 2), "reason": "Neutral"}
            scores.append(0)

        # --- Golden/Death Cross ---
        if sma_50 > 0 and sma_200 > 0:
            if sma_50 > sma_200:
                signals["MA_Cross"] = {"signal": "BUY", "value": round(sma_50 / sma_200, 4), "reason": "Golden Cross (SMA50>SMA200)"}
                scores.append(1)
            else:
                signals["MA_Cross"] = {"signal": "SELL", "value": round(sma_50 / sma_200, 4), "reason": "Death Cross (SMA50<SMA200)"}
                scores.append(-1)

        # --- Overall Signal ---
        avg_score = np.mean(scores) if scores else 0
        if avg_score >= 0.5:
            overall = "STRONG BUY"
        elif avg_score >= 0.2:
            overall = "BUY"
        elif avg_score <= -0.5:
            overall = "STRONG SELL"
        elif avg_score <= -0.2:
            overall = "SELL"
        else:
            overall = "HOLD"

        # --- Key Values ---
        indicator_values = {
            "RSI": round(rsi, 2),
            "MACD": round(macd, 4),
            "SMA_20": round(sma_20, 2),
            "SMA_50": round(sma_50, 2),
            "SMA_200": round(sma_200, 2),
            "EMA_12": round(latest.get("EMA_12", 0), 2),
            "EMA_26": round(latest.get("EMA_26", 0), 2),
            "BB_Upper": round(latest.get("BB_Upper", 0), 2),
            "BB_Lower": round(latest.get("BB_Lower", 0), 2),
            "BB_Middle": round(latest.get("BB_Middle", 0), 2),
            "ATR": round(latest.get("ATR", 0), 2),
            "Volatility": round(latest.get("Volatility_20", 0), 4),
            "Stoch_K": round(stoch_k, 2),
            "Stoch_D": round(stoch_d, 2),
        }

        return {
            "signals": signals,
            "overall_signal": overall,
            "signal_score": round(avg_score, 3),
            "indicator_values": indicator_values,
        }

    def fibonacci_retracement(self, df: pd.DataFrame, period_days: int = 252) -> Dict:
        """Calculate Fibonacci retracement levels"""
        recent = df.tail(period_days)
        high = float(recent["High"].max())
        low = float(recent["Low"].min())
        diff = high - low

        return {
            "high": round(high, 2),
            "low": round(low, 2),
            "level_0": round(high, 2),
            "level_236": round(high - 0.236 * diff, 2),
            "level_382": round(high - 0.382 * diff, 2),
            "level_500": round(high - 0.500 * diff, 2),
            "level_618": round(high - 0.618 * diff, 2),
            "level_100": round(low, 2),
        }
