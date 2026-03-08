"""
Enhanced backtesting engine with multiple strategies
"""
import numpy as np
import pandas as pd
from typing import Dict, List
from backend.utils.data_fetcher import DataFetcher
from backend.utils.feature_engineering import FeatureEngineer


class Backtester:
    """Tests trading strategies on historical data"""

    def __init__(self):
        self.fetcher = DataFetcher()
        self.engineer = FeatureEngineer()

    def run_all_strategies(self, ticker: str, initial_capital: float = 100000) -> Dict:
        """Run all strategies and return comparison"""
        df = self.fetcher.fetch_stock_data(ticker, period="2y")
        df = self.engineer.compute_technical_indicators(df)
        df = df.dropna()

        results = {}

        strategies = [
            ("SMA Crossover", self._sma_crossover_strategy),
            ("RSI Strategy", self._rsi_strategy),
            ("MACD Strategy", self._macd_strategy),
            ("Buy & Hold", self._buy_and_hold),
        ]

        for name, strategy_fn in strategies:
            try:
                result = strategy_fn(df.copy(), initial_capital)
                results[name] = result
            except Exception as e:
                results[name] = self._default_result(initial_capital)

        return results

    def run_backtest(self, ticker: str, strategy: str = "sma", initial_capital: float = 100000) -> Dict:
        """Run a single strategy backtest"""
        df = self.fetcher.fetch_stock_data(ticker, period="2y")
        df = self.engineer.compute_technical_indicators(df)
        df = df.dropna()

        strategy_map = {
            "sma": self._sma_crossover_strategy,
            "rsi": self._rsi_strategy,
            "macd": self._macd_strategy,
            "buyhold": self._buy_and_hold,
        }

        fn = strategy_map.get(strategy.lower(), self._sma_crossover_strategy)
        return fn(df, initial_capital)

    def _sma_crossover_strategy(self, df: pd.DataFrame, initial_capital: float) -> Dict:
        """SMA 20/50 crossover strategy"""
        capital = initial_capital
        position = 0
        trades = []
        portfolio_values = []

        for i in range(1, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i - 1]
            price = row["Close"]

            if pd.isna(row["SMA_20"]) or pd.isna(row["SMA_50"]):
                portfolio_values.append(capital + position * price)
                continue

            # Buy signal
            if prev_row["SMA_20"] <= prev_row["SMA_50"] and row["SMA_20"] > row["SMA_50"] and position == 0:
                shares = capital // price
                if shares > 0:
                    position = shares
                    capital -= shares * price
                    trades.append({"type": "BUY", "price": price, "date": str(row.get("Date", ""))[:10]})

            # Sell signal
            elif prev_row["SMA_20"] >= prev_row["SMA_50"] and row["SMA_20"] < row["SMA_50"] and position > 0:
                capital += position * price
                trades.append({"type": "SELL", "price": price, "date": str(row.get("Date", ""))[:10]})
                position = 0

            portfolio_values.append(capital + position * price)

        # Close any open position
        if position > 0:
            capital += position * df.iloc[-1]["Close"]

        return self._compute_metrics("SMA Crossover", initial_capital, capital, trades, portfolio_values)

    def _rsi_strategy(self, df: pd.DataFrame, initial_capital: float) -> Dict:
        """RSI-based strategy: buy on oversold, sell on overbought"""
        capital = initial_capital
        position = 0
        trades = []
        portfolio_values = []

        for i in range(len(df)):
            row = df.iloc[i]
            price = row["Close"]
            rsi = row.get("RSI", 50)

            if pd.isna(rsi):
                portfolio_values.append(capital + position * price)
                continue

            if rsi < 30 and position == 0:
                shares = capital // price
                if shares > 0:
                    position = shares
                    capital -= shares * price
                    trades.append({"type": "BUY", "price": price, "date": str(row.get("Date", ""))[:10]})

            elif rsi > 70 and position > 0:
                capital += position * price
                trades.append({"type": "SELL", "price": price, "date": str(row.get("Date", ""))[:10]})
                position = 0

            portfolio_values.append(capital + position * price)

        if position > 0:
            capital += position * df.iloc[-1]["Close"]

        return self._compute_metrics("RSI Strategy", initial_capital, capital, trades, portfolio_values)

    def _macd_strategy(self, df: pd.DataFrame, initial_capital: float) -> Dict:
        """MACD crossover strategy"""
        capital = initial_capital
        position = 0
        trades = []
        portfolio_values = []

        for i in range(1, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i - 1]
            price = row["Close"]

            if pd.isna(row.get("MACD")) or pd.isna(row.get("MACD_Signal")):
                portfolio_values.append(capital + position * price)
                continue

            if prev_row["MACD"] <= prev_row["MACD_Signal"] and row["MACD"] > row["MACD_Signal"] and position == 0:
                shares = capital // price
                if shares > 0:
                    position = shares
                    capital -= shares * price
                    trades.append({"type": "BUY", "price": price, "date": str(row.get("Date", ""))[:10]})

            elif prev_row["MACD"] >= prev_row["MACD_Signal"] and row["MACD"] < row["MACD_Signal"] and position > 0:
                capital += position * price
                trades.append({"type": "SELL", "price": price, "date": str(row.get("Date", ""))[:10]})
                position = 0

            portfolio_values.append(capital + position * price)

        if position > 0:
            capital += position * df.iloc[-1]["Close"]

        return self._compute_metrics("MACD Strategy", initial_capital, capital, trades, portfolio_values)

    def _buy_and_hold(self, df: pd.DataFrame, initial_capital: float) -> Dict:
        """Buy and hold benchmark"""
        start_price = df.iloc[0]["Close"]
        end_price = df.iloc[-1]["Close"]
        shares = initial_capital / start_price
        final_capital = shares * end_price

        total_return = (final_capital - initial_capital) / initial_capital * 100
        portfolio_values = [initial_capital * (row["Close"] / start_price) for _, row in df.iterrows()]

        returns = pd.Series(portfolio_values).pct_change().dropna()
        sharpe = float(np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0

        prices = np.array(portfolio_values)
        peak = np.maximum.accumulate(prices)
        drawdown = (peak - prices) / peak * 100
        max_dd = float(np.max(drawdown))

        return {
            "strategy": "Buy & Hold",
            "initial_capital": initial_capital,
            "final_capital": round(final_capital, 2),
            "total_return": round(total_return, 2),
            "sharpe_ratio": round(sharpe, 3),
            "max_drawdown": round(max_dd, 2),
            "win_rate": 100.0,
            "total_trades": 1,
            "portfolio_values": [round(v, 2) for v in portfolio_values[-60:]],
        }

    def _compute_metrics(self, strategy: str, initial_capital: float, final_capital: float,
                          trades: List, portfolio_values: List) -> Dict:
        """Compute performance metrics"""
        total_return = (final_capital - initial_capital) / initial_capital * 100

        buy_trades = [t for t in trades if t["type"] == "BUY"]
        sell_trades = [t for t in trades if t["type"] == "SELL"]

        wins = 0
        for i in range(min(len(buy_trades), len(sell_trades))):
            if sell_trades[i]["price"] > buy_trades[i]["price"]:
                wins += 1

        total_trade_pairs = min(len(buy_trades), len(sell_trades))
        win_rate = (wins / total_trade_pairs * 100) if total_trade_pairs > 0 else 0

        if portfolio_values:
            pv = np.array(portfolio_values)
            returns = pd.Series(pv).pct_change().dropna()
            sharpe = float(np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0

            peak = np.maximum.accumulate(pv)
            drawdown = np.where(peak > 0, (peak - pv) / peak * 100, 0)
            max_dd = float(np.max(drawdown))
        else:
            sharpe = 0.0
            max_dd = 0.0

        return {
            "strategy": strategy,
            "initial_capital": initial_capital,
            "final_capital": round(final_capital, 2),
            "total_return": round(total_return, 2),
            "sharpe_ratio": round(sharpe, 3),
            "max_drawdown": round(max_dd, 2),
            "win_rate": round(win_rate, 1),
            "total_trades": len(trades),
            "portfolio_values": [round(v, 2) for v in portfolio_values[-60:]],
        }

    def _default_result(self, initial_capital: float) -> Dict:
        return {
            "strategy": "N/A",
            "initial_capital": initial_capital,
            "final_capital": initial_capital,
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "total_trades": 0,
            "portfolio_values": [],
        }
