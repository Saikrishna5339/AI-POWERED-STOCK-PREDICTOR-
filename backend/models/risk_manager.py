"""
Risk analysis module for Indian stock market
"""
import numpy as np
import pandas as pd
from typing import Dict
from backend.utils.data_fetcher import DataFetcher


class RiskManager:
    """Calculates comprehensive risk metrics for Indian stocks"""

    def __init__(self):
        self.data_fetcher = DataFetcher()

    def calculate_all_metrics(self, ticker: str) -> Dict:
        """
        Calculate all risk metrics for a stock

        Returns:
            Complete risk analysis dictionary
        """
        try:
            df = self.data_fetcher.fetch_stock_data(ticker, period="2y")
            df["Returns"] = df["Close"].pct_change()
            df = df.dropna()

            current_price = float(df["Close"].iloc[-1])
            returns = df["Returns"].values

            # Volatility (annualized)
            volatility = float(np.std(returns) * np.sqrt(252) * 100)

            # Sharpe Ratio (assuming 6% risk-free rate for India)
            risk_free_rate = 0.06 / 252
            excess_returns = returns - risk_free_rate
            sharpe = float(np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)) if np.std(excess_returns) > 0 else 0

            # Beta (vs NIFTY 50)
            beta = self._calculate_beta(df)

            # Maximum Drawdown
            max_drawdown = self._calculate_max_drawdown(df["Close"].values)

            # Value at Risk (95% confidence, 1-day)
            var_95 = float(np.percentile(returns, 5) * 100)

            # Sortino Ratio
            negative_returns = returns[returns < 0]
            downside_std = float(np.std(negative_returns)) if len(negative_returns) > 0 else 0.01
            sortino = float(np.mean(returns) / downside_std * np.sqrt(252)) if downside_std > 0 else 0

            # Risk score (0-100)
            risk_score = self._calculate_risk_score(volatility, beta, max_drawdown)

            # Risk level
            risk_level = self._get_risk_level(risk_score)

            # Stop loss suggestion
            stop_loss = self._suggest_stop_loss(current_price, volatility / 100)

            # Support and resistance levels
            support, resistance = self._get_support_resistance(df)

            return {
                "volatility": round(volatility, 2),
                "sharpe_ratio": round(sharpe, 3),
                "sortino_ratio": round(sortino, 3),
                "beta": round(beta, 3),
                "max_drawdown": round(max_drawdown, 2),
                "var_95": round(var_95, 2),
                "risk_score": round(risk_score, 1),
                "risk_level": risk_level,
                "stop_loss": round(stop_loss, 2),
                "support_level": round(support, 2),
                "resistance_level": round(resistance, 2),
                "current_price": round(current_price, 2),
            }

        except Exception as e:
            print(f"Risk calculation error: {e}")
            return self._default_risk()

    def _calculate_beta(self, df: pd.DataFrame) -> float:
        """Calculate beta against NIFTY 50"""
        try:
            import yfinance as yf
            nifty = yf.Ticker("^NSEI")
            nifty_hist = nifty.history(period="2y")
            if nifty_hist.empty:
                return 1.0
            nifty_returns = nifty_hist["Close"].pct_change().dropna()

            # Align dates
            stock_returns = df.set_index("Date")["Returns"].dropna()
            stock_returns.index = pd.to_datetime(stock_returns.index).tz_localize(None)
            nifty_returns.index = pd.to_datetime(nifty_returns.index).tz_localize(None)

            aligned = pd.concat([stock_returns, nifty_returns], axis=1, join="inner")
            aligned.columns = ["stock", "market"]
            aligned = aligned.dropna()

            if len(aligned) < 20:
                return 1.0

            cov = np.cov(aligned["stock"], aligned["market"])
            beta = cov[0, 1] / cov[1, 1]
            return float(np.clip(beta, -3, 5))
        except Exception:
            return 1.0

    def _calculate_max_drawdown(self, prices: np.ndarray) -> float:
        """Calculate maximum drawdown in percentage"""
        peak = prices[0]
        max_dd = 0
        for price in prices:
            if price > peak:
                peak = price
            dd = (peak - price) / peak * 100
            if dd > max_dd:
                max_dd = dd
        return float(max_dd)

    def _calculate_risk_score(self, volatility: float, beta: float, max_drawdown: float) -> float:
        """Calculate composite risk score 0-100"""
        # Volatility contributes 40% (typical range 10-60%)
        vol_score = min(volatility / 60, 1.0) * 40

        # Beta contributes 30% (range 0-2)
        beta_score = min(abs(beta) / 2, 1.0) * 30

        # Max drawdown contributes 30% (range 0-60%)
        dd_score = min(max_drawdown / 60, 1.0) * 30

        return min(vol_score + beta_score + dd_score, 100)

    def _get_risk_level(self, risk_score: float) -> str:
        if risk_score < 33:
            return "Low Risk"
        elif risk_score < 66:
            return "Medium Risk"
        else:
            return "High Risk"

    def _suggest_stop_loss(self, price: float, daily_vol: float) -> float:
        """Suggest stop loss at 2x daily ATR"""
        atr = price * daily_vol * np.sqrt(14)  # 14-day ATR approximation
        return max(price - 2 * atr, price * 0.85)

    def _get_support_resistance(self, df: pd.DataFrame) -> tuple:
        """Simple support and resistance levels"""
        recent = df.tail(60)
        support = float(recent["Low"].min())
        resistance = float(recent["High"].max())
        return support, resistance

    def _default_risk(self) -> Dict:
        return {
            "volatility": 25.0,
            "sharpe_ratio": 0.5,
            "sortino_ratio": 0.7,
            "beta": 1.0,
            "max_drawdown": 20.0,
            "var_95": -2.5,
            "risk_score": 50.0,
            "risk_level": "Medium Risk",
            "stop_loss": 0.0,
            "support_level": 0.0,
            "resistance_level": 0.0,
            "current_price": 0.0,
        }
