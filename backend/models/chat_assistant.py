"""
AI Chat Assistant for stock market queries
"""
import re
from typing import Dict, List
from backend.utils.data_fetcher import DataFetcher


class ChatAssistant:
    """Answers stock market questions using available data and predictions"""

    def __init__(self):
        self.fetcher = DataFetcher()
        # Common Indian stock name aliases
        self.stock_aliases = {
            "reliance": "RELIANCE",
            "tcs": "TCS",
            "infosys": "INFY",
            "infy": "INFY",
            "hdfc bank": "HDFCBANK",
            "hdfcbank": "HDFCBANK",
            "icici": "ICICIBANK",
            "sbi": "SBIN",
            "wipro": "WIPRO",
            "hcl": "HCLTECH",
            "bajaj finance": "BAJFINANCE",
            "bajajfinance": "BAJFINANCE",
            "maruti": "MARUTI",
            "tatamotors": "TATAMOTORS",
            "tata motors": "TATAMOTORS",
            "sunpharma": "SUNPHARMA",
            "sun pharma": "SUNPHARMA",
            "itc": "ITC",
            "ongc": "ONGC",
            "ntpc": "NTPC",
            "titan": "TITAN",
            "airtel": "BHARTIARTL",
            "bhartiartl": "BHARTIARTL",
            "adani": "ADANIENT",
            "kotak": "KOTAKBANK",
            "asian paints": "ASIANPAINT",
            "asianpaint": "ASIANPAINT",
            "techm": "TECHM",
            "tech mahindra": "TECHM",
        }

    def process_message(self, message: str) -> Dict:
        """
        Process user message and return response with data

        Returns:
            response dict with message and optionally chart_data
        """
        message_lower = message.lower().strip()

        # Extract ticker if mentioned
        ticker = self._extract_ticker(message_lower)

        # Intent detection
        if any(w in message_lower for w in ["predict", "price tomorrow", "next day", "forecast"]):
            return self._handle_prediction(ticker, message)

        elif any(w in message_lower for w in ["buy", "invest", "good investment", "should i buy"]):
            return self._handle_recommendation(ticker, message)

        elif any(w in message_lower for w in ["technical", "rsi", "macd", "indicator", "signal"]):
            return self._handle_technical(ticker, message)

        elif any(w in message_lower for w in ["news", "sentiment", "latest", "update"]):
            return self._handle_news(ticker, message)

        elif any(w in message_lower for w in ["risk", "volatile", "safe", "beta", "sharpe"]):
            return self._handle_risk(ticker, message)

        elif any(w in message_lower for w in ["top", "best", "trending", "gainers", "losers"]):
            return self._handle_market_overview(message)

        elif any(w in message_lower for w in ["nifty", "sensex", "bank nifty", "market", "index"]):
            return self._handle_market_indices(message)

        elif any(w in message_lower for w in ["hello", "hi", "help", "what can you", "how to"]):
            return self._handle_greeting()

        else:
            if ticker:
                return self._handle_stock_info(ticker, message)
            return self._handle_unknown(message)

    def _extract_ticker(self, message: str) -> str:
        """Extract stock ticker from message"""
        # Check aliases
        for alias, ticker in self.stock_aliases.items():
            if alias in message:
                return ticker

        # Check for .NS pattern
        ns_match = re.search(r'\b([A-Z]{2,10})\.NS\b', message.upper())
        if ns_match:
            return ns_match.group(1)

        # Look for uppercase stock codes
        words = message.upper().split()
        for word in words:
            word_clean = re.sub(r'[^A-Z0-9&]', '', word)
            if 3 <= len(word_clean) <= 12 and word_clean.isupper():
                # Filter out common English words
                skip_words = {"THE", "AND", "FOR", "BUY", "SELL", "TOP", "RSI", "MACD",
                              "SMA", "EMA", "WHAT", "SHOW", "GIVE", "GET", "HOW", "CAN",
                              "NIFTY", "BANK", "GOOD", "BAD", "HIGH", "LOW"}
                if word_clean not in skip_words:
                    return word_clean

        return ""

    def _handle_prediction(self, ticker: str, message: str) -> Dict:
        """Handle prediction query"""
        if not ticker:
            return {"message": "🤔 Please mention a stock name, e.g., 'Predict RELIANCE stock'", "type": "info"}
        try:
            from backend.models.lstm_model import StockPredictor
            predictor = StockPredictor()
            data = predictor.predict_stock(ticker)
            cp = data["current_price"]
            nd = data["next_day_price"]
            ch = data["price_change_pct"]
            direction = "📈" if ch > 0 else "📉"
            return {
                "message": f"""**{ticker} Price Prediction**

{direction} Current Price: **Rs.{cp:,.2f}**
🎯 Next Day Prediction: **Rs.{nd:,.2f}** ({'+' if ch >= 0 else ''}{ch:.2f}%)
📅 Next Week Trend: Rs.{data['next_week_trend']:,.2f}
📆 Next Month Trend: Rs.{data['next_month_trend']:,.2f}

🤖 Model: {data['model_used']}
📊 Confidence: {data['confidence_score']:.0f}%
📉 RMSE: Rs.{data['rmse']:.2f}

_Disclaimer: Not financial advice_""",
                "type": "prediction",
                "data": {"ticker": ticker, "prediction": data},
            }
        except Exception as e:
            return {"message": f"[WARN]️ Could not predict {ticker}: {str(e)}", "type": "error"}

    def _handle_recommendation(self, ticker: str, message: str) -> Dict:
        """Handle buy/sell recommendation query"""
        if not ticker:
            return {"message": "Please specify a stock, e.g., 'Is TCS a good investment?'", "type": "info"}
        try:
            from backend.models.lstm_model import StockPredictor
            from backend.models.risk_manager import RiskManager
            predictor = StockPredictor()
            risk_mgr = RiskManager()
            pred_data = predictor.predict_stock(ticker)
            risk_data = risk_mgr.calculate_all_metrics(ticker)
            rec = predictor.generate_ai_recommendation(pred_data, risk_data)

            emoji_map = {"STRONG BUY": "🟢", "BUY": "🟩", "HOLD": "🟡", "SELL": "🔴", "STRONG SELL": "🔴"}
            emoji = emoji_map.get(rec["recommendation"], "⚪")
            reasons_str = "\n".join([f"• {r}" for r in rec.get("reasons", [])])

            return {
                "message": f"""**{ticker} AI Recommendation**

{emoji} **{rec['recommendation']}**
📊 Confidence: {rec['confidence']:.0f}%

**Why:**
{reasons_str}

[WARN]️ *{rec['disclaimer']}*""",
                "type": "recommendation",
            }
        except Exception as e:
            return {"message": f"[WARN]️ Could not get recommendation for {ticker}: {str(e)}", "type": "error"}

    def _handle_technical(self, ticker: str, message: str) -> Dict:
        """Handle technical analysis query"""
        if not ticker:
            return {"message": "Please specify a stock for technical analysis.", "type": "info"}
        try:
            from backend.utils.feature_engineering import FeatureEngineer
            from backend.utils.data_fetcher import DataFetcher
            fe = FeatureEngineer()
            df = DataFetcher().fetch_stock_data(ticker)
            ta = fe.get_technical_signals(df)
            iv = ta["indicator_values"]
            signals = ta["signals"]

            sig_lines = []
            for name, sig in signals.items():
                sig_lines.append(f"• **{name}**: {sig['signal']} ({sig.get('reason', '')})")

            return {
                "message": f"""**{ticker} Technical Analysis**

📊 Overall Signal: **{ta['overall_signal']}**

**Key Indicators:**
• RSI: {iv['RSI']} | MACD: {iv['MACD']}
• SMA 20: Rs.{iv['SMA_20']} | SMA 50: Rs.{iv['SMA_50']}
• BB Upper: Rs.{iv['BB_Upper']} | BB Lower: Rs.{iv['BB_Lower']}
• Stoch K: {iv['Stoch_K']} | Stoch D: {iv['Stoch_D']}

**Signals:**
{chr(10).join(sig_lines)}""",
                "type": "technical",
            }
        except Exception as e:
            return {"message": f"[WARN]️ Technical analysis error: {str(e)}", "type": "error"}

    def _handle_news(self, ticker: str, message: str) -> Dict:
        """Handle news query"""
        if not ticker:
            return {"message": "Please specify a stock for news, e.g., 'Show news for INFY'", "type": "info"}
        try:
            from backend.utils.sentiment_analyzer import SentimentAnalyzer
            news = self.fetcher.fetch_news(ticker, num_articles=5)
            analyzer = SentimentAnalyzer()
            sentiment = analyzer.analyze_news_batch(news)

            news_lines = []
            for article in news[:5]:
                news_lines.append(f"• {article['title'][:80]}...")

            return {
                "message": f"""**{ticker} Latest News & Sentiment**

😊 Overall Sentiment: **{sentiment['sentiment_label']}** ({sentiment['sentiment_score']:.2f})

📰 Recent Headlines:
{chr(10).join(news_lines)}""",
                "type": "news",
            }
        except Exception as e:
            return {"message": f"[WARN]️ News fetch error: {str(e)}", "type": "error"}

    def _handle_risk(self, ticker: str, message: str) -> Dict:
        """Handle risk analysis query"""
        if not ticker:
            return {"message": "Please specify a stock for risk analysis.", "type": "info"}
        try:
            from backend.models.risk_manager import RiskManager
            risk = RiskManager().calculate_all_metrics(ticker)
            return {
                "message": f"""**{ticker} Risk Analysis**

[WARN]️ Risk Level: **{risk['risk_level']}** ({risk['risk_score']:.0f}/100)

📊 Key Metrics:
• Volatility: {risk['volatility']:.2f}% (annualized)
• Beta vs NIFTY: {risk['beta']:.2f}
• Sharpe Ratio: {risk['sharpe_ratio']:.2f}
• Sortino Ratio: {risk['sortino_ratio']:.2f}
• Max Drawdown: -{risk['max_drawdown']:.1f}%
• VaR (95%): {risk['var_95']:.2f}%

🛡️ Stop Loss: Rs.{risk['stop_loss']:,.2f}
📈 Resistance: Rs.{risk['resistance_level']:,.2f}
📉 Support: Rs.{risk['support_level']:,.2f}""",
                "type": "risk",
            }
        except Exception as e:
            return {"message": f"[WARN]️ Risk analysis error: {str(e)}", "type": "error"}

    def _handle_stock_info(self, ticker: str, message: str) -> Dict:
        """Handle general stock info query"""
        try:
            info = self.fetcher.fetch_stock_info(ticker)
            ch_arrow = "▲" if info["change_pct"] >= 0 else "▼"
            return {
                "message": f"""**{info['name']} ({ticker})**
🏭 Sector: {info['sector']} | {info['industry']}

💰 Current: **Rs.{info['current_price']:,.2f}** {ch_arrow} {info['change_pct']:+.2f}%
📊 Open: Rs.{info['open_price']:,.2f} | Close: Rs.{info['previous_close']:,.2f}
📈 High: Rs.{info['day_high']:,.2f} | Low: Rs.{info['day_low']:,.2f}
📉 52W High: Rs.{info['week52_high']:,.2f} | 52W Low: Rs.{info['week52_low']:,.2f}
📦 Volume: {info['volume']:,}
💎 P/E Ratio: {info['pe_ratio']} | Market Cap: Rs.{info['market_cap']:,.0f}""",
                "type": "stock_info",
                "data": info,
            }
        except Exception as e:
            return {"message": f"[WARN]️ Could not fetch info for {ticker}: {str(e)}", "type": "error"}

    def _handle_market_indices(self, message: str) -> Dict:
        """Handle market indices query"""
        try:
            indices = self.fetcher.fetch_index_data()
            lines = []
            for idx in indices:
                arrow = "▲" if idx["change_pct"] >= 0 else "▼"
                lines.append(f"• **{idx['name']}**: {idx['price']:,.2f} {arrow} {idx['change_pct']:+.2f}%")
            return {
                "message": f"""**Indian Market Indices**

{chr(10).join(lines)}""",
                "type": "indices",
            }
        except Exception as e:
            return {"message": f"[WARN]️ Could not fetch market data: {str(e)}", "type": "error"}

    def _handle_market_overview(self, message: str) -> Dict:
        """Handle market overview / sector query"""
        return {
            "message": """**Market Overview**

📊 Check the **Heatmap** tab to see sector performance.

🔥 Top sectors to watch:
• Banking - HDFC, ICICI, SBI
• IT - TCS, Infosys, Wipro
• Energy - Reliance, ONGC
• Pharma - Sun Pharma, Dr. Reddy's

💡 Type a stock name for detailed analysis!""",
            "type": "overview",
        }

    def _handle_greeting(self) -> Dict:
        return {
            "message": """👋 **Hello! I'm your AI Stock Market Assistant**

I can help you with:
• 📈 **Predict** - "Predict RELIANCE stock"
• 💡 **Recommend** - "Is TCS a good investment?"
• 📊 **Technicals** - "Show technical analysis for INFY"
• 📰 **News** - "Latest news for HDFC Bank"
• [WARN]️ **Risk** - "What's the risk of BAJFINANCE?"
• 📉 **Indices** - "How is NIFTY today?"
• 💰 **Info** - Just type any stock name like "WIPRO"

_Powered by LSTM AI & Technical Analysis_""",
            "type": "greeting",
        }

    def _handle_unknown(self, message: str) -> Dict:
        return {
            "message": """🤔 I didn't quite understand that.

Try asking:
• "Predict RELIANCE price"
• "Is INFY a good buy?"
• "Show risk for TCS"
• "HDFC Bank news"
• "How is NIFTY today?"

Or type a stock symbol directly like **TATAMOTORS**""",
            "type": "help",
        }
