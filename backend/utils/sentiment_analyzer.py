"""
Sentiment analysis using VADER (fast, no heavy model downloads required)
with optional FinBERT for better accuracy when available
"""
import re
from typing import List, Dict
import numpy as np


class SentimentAnalyzer:
    """Analyzes financial news sentiment"""

    def __init__(self):
        self.vader = None
        self._init_vader()

    def _init_vader(self):
        """Initialize VADER sentiment analyzer"""
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self.vader = SentimentIntensityAnalyzer()

            # Add financial domain words
            self.vader.lexicon.update({
                "bullish": 2.5,
                "bearish": -2.5,
                "rally": 2.0,
                "surge": 2.0,
                "soar": 2.0,
                "plunge": -2.5,
                "crash": -3.0,
                "slump": -2.0,
                "downturn": -2.0,
                "upturn": 2.0,
                "outperform": 2.0,
                "underperform": -2.0,
                "downgrade": -2.5,
                "upgrade": 2.5,
                "buy": 1.5,
                "sell": -1.5,
                "hold": 0.0,
                "profit": 2.0,
                "loss": -2.0,
                "earnings beat": 2.5,
                "earnings miss": -2.5,
                "dividend": 1.5,
                "buyback": 1.5,
                "acquisition": 1.0,
                "merger": 0.5,
                "bankruptcy": -3.0,
                "debt": -1.0,
                "revenue growth": 2.0,
                "revenue decline": -2.0,
            })
            print("[OK] VADER sentiment analyzer initialized")
        except ImportError:
            print("[WARN] VADER not available. Install: pip install vaderSentiment")
            self.vader = None

    def analyze_text(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of a single text

        Returns:
            Dictionary with positive, negative, neutral, compound scores
        """
        if not text or not text.strip():
            return {"positive": 0.33, "negative": 0.33, "neutral": 0.34, "sentiment_score": 0.0}

        if self.vader:
            return self._vader_analyze(text)
        else:
            return self._keyword_analyze(text)

    def _vader_analyze(self, text: str) -> Dict[str, float]:
        """Use VADER for sentiment analysis"""
        try:
            scores = self.vader.polarity_scores(text)
            compound = scores["compound"]

            # Map compound (-1 to 1) to positive/negative/neutral probs
            if compound >= 0.05:
                positive = 0.5 + compound * 0.5
                negative = (1 - positive) * 0.3
                neutral = 1 - positive - negative
            elif compound <= -0.05:
                negative = 0.5 + abs(compound) * 0.5
                positive = (1 - negative) * 0.3
                neutral = 1 - positive - negative
            else:
                neutral = 0.6
                positive = 0.2
                negative = 0.2

            return {
                "positive": round(max(0, min(1, positive)), 3),
                "negative": round(max(0, min(1, negative)), 3),
                "neutral": round(max(0, min(1, neutral)), 3),
                "sentiment_score": round(compound, 3),
            }
        except Exception as e:
            return {"positive": 0.33, "negative": 0.33, "neutral": 0.34, "sentiment_score": 0.0}

    def _keyword_analyze(self, text: str) -> Dict[str, float]:
        """Fallback keyword-based sentiment"""
        text_lower = text.lower()

        positive_words = [
            "bullish", "surge", "rally", "gain", "profit", "growth",
            "strong", "outperform", "upgrade", "buy", "positive", "rise",
            "high", "beat", "record", "best", "excellent"
        ]
        negative_words = [
            "bearish", "plunge", "crash", "loss", "decline", "weak",
            "underperform", "downgrade", "sell", "negative", "fall",
            "low", "miss", "worst", "poor", "concern"
        ]

        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        total = pos_count + neg_count

        if total == 0:
            return {"positive": 0.33, "negative": 0.33, "neutral": 0.34, "sentiment_score": 0.0}

        pos = pos_count / (total + 2)
        neg = neg_count / (total + 2)
        neu = 1 - pos - neg
        score = pos - neg

        return {
            "positive": round(pos, 3),
            "negative": round(neg, 3),
            "neutral": round(neu, 3),
            "sentiment_score": round(score, 3),
        }

    def analyze_news_batch(self, news_articles: List[Dict]) -> Dict:
        """
        Analyze sentiment of multiple news articles

        Returns:
            Aggregated sentiment scores with sentiment strength
        """
        if not news_articles:
            return {
                "positive": 0.33,
                "negative": 0.33,
                "neutral": 0.34,
                "sentiment_score": 0.0,
                "sentiment_strength": 0.0,
                "sentiment_label": "Neutral",
                "articles_analyzed": 0,
            }

        sentiments = []
        for article in news_articles:
            text = f"{article.get('title', '')} {article.get('description', '')}"
            if text.strip():
                sentiment = self.analyze_text(text)
                sentiments.append(sentiment)

        if not sentiments:
            return {
                "positive": 0.33,
                "negative": 0.33,
                "neutral": 0.34,
                "sentiment_score": 0.0,
                "sentiment_strength": 0.0,
                "sentiment_label": "Neutral",
                "articles_analyzed": 0,
            }

        avg_positive = float(np.mean([s["positive"] for s in sentiments]))
        avg_negative = float(np.mean([s["negative"] for s in sentiments]))
        avg_neutral = float(np.mean([s["neutral"] for s in sentiments]))
        avg_score = float(np.mean([s["sentiment_score"] for s in sentiments]))
        sentiment_strength = float(abs(avg_score))

        # Determine label
        if avg_score > 0.15:
            label = "Positive" if avg_score < 0.5 else "Very Positive"
        elif avg_score < -0.15:
            label = "Negative" if avg_score > -0.5 else "Very Negative"
        else:
            label = "Neutral"

        return {
            "positive": round(avg_positive, 3),
            "negative": round(avg_negative, 3),
            "neutral": round(avg_neutral, 3),
            "sentiment_score": round(avg_score, 3),
            "sentiment_strength": round(sentiment_strength, 3),
            "sentiment_label": label,
            "articles_analyzed": len(sentiments),
        }
