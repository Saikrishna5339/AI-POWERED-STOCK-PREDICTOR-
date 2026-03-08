"""
Ensemble predictor combining LSTM, Transformer, and Sentiment
"""
import numpy as np
from typing import Dict, Tuple
from backend.models.lstm_model import LSTMModel
from backend.models.transformer_model import TransformerModel
from backend.utils.sentiment_analyzer import SentimentAnalyzer
from backend.utils.data_fetcher import DataFetcher
from backend.utils.feature_engineering import FeatureEngineer
from backend.config import (
    LSTM_WEIGHT, TRANSFORMER_WEIGHT, SENTIMENT_WEIGHT,
    LOOKBACK_WINDOW
)


class EnsemblePredictor:
    """Ensemble prediction combining multiple models"""
    
    def __init__(self):
        """Initialize ensemble components"""
        self.lstm_model = LSTMModel(lookback=LOOKBACK_WINDOW, n_features=5)
        self.transformer_model = TransformerModel(lookback=LOOKBACK_WINDOW, n_features=5)
        self.sentiment_analyzer = SentimentAnalyzer()
        self.data_fetcher = DataFetcher()
        self.feature_engineer = FeatureEngineer()
        
        self.lstm_weight = LSTM_WEIGHT
        self.transformer_weight = TRANSFORMER_WEIGHT
        self.sentiment_weight = SENTIMENT_WEIGHT
    
    def prepare_prediction_data(self, ticker: str) -> Tuple[np.ndarray, float, Dict]:
        """
        Prepare data for prediction
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Tuple of (sequence_data, current_price, sentiment_data)
        """
        # Fetch stock data
        df = self.data_fetcher.fetch_stock_data(ticker, period="1y")
        
        # Get current price
        current_price = self.data_fetcher.get_current_price(ticker)
        
        # Prepare features
        df = self.feature_engineer.prepare_features(df)
        
        # Select feature columns
        feature_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Scale data
        scaled_data = self.feature_engineer.scale_data(df, feature_columns)
        
        # Get last sequence for prediction
        if len(scaled_data) < LOOKBACK_WINDOW:
            raise ValueError(f"Insufficient data for prediction. Need at least {LOOKBACK_WINDOW} days.")
        
        last_sequence = scaled_data[-LOOKBACK_WINDOW:]
        last_sequence = np.expand_dims(last_sequence, axis=0)
        
        # Fetch and analyze news sentiment
        news_articles = self.data_fetcher.fetch_news(ticker)
        sentiment_data = self.sentiment_analyzer.analyze_news_batch(news_articles)
        
        return last_sequence, current_price, sentiment_data
    
    def predict(self, ticker: str) -> Dict:
        """
        Make ensemble prediction
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with all predictions and metadata
        """
        # Prepare data
        sequence_data, current_price, sentiment_data = self.prepare_prediction_data(ticker)
        
        # LSTM prediction
        lstm_pred_scaled = self.lstm_model.predict(sequence_data)[0][0]
        lstm_prediction = self.feature_engineer.inverse_scale_prediction(lstm_pred_scaled)
        
        # Transformer prediction
        transformer_pred_scaled = self.transformer_model.predict(sequence_data)[0][0]
        transformer_prediction = self.feature_engineer.inverse_scale_prediction(transformer_pred_scaled)
        
        # Sentiment-adjusted price
        sentiment_score = sentiment_data['sentiment_score']
        sentiment_adjusted_price = current_price * (1 + sentiment_score * 0.01)
        
        # Ensemble prediction
        final_prediction = (
            self.lstm_weight * lstm_prediction +
            self.transformer_weight * transformer_prediction +
            self.sentiment_weight * sentiment_adjusted_price
        )
        
        # Calculate model agreement (confidence indicator)
        predictions = [lstm_prediction, transformer_prediction, sentiment_adjusted_price]
        prediction_std = np.std(predictions)
        prediction_mean = np.mean(predictions)
        model_agreement = 1 - min(prediction_std / prediction_mean, 1.0) if prediction_mean > 0 else 0
        
        return {
            'ticker': ticker,
            'current_price': float(current_price),
            'lstm_prediction': float(lstm_prediction),
            'transformer_prediction': float(transformer_prediction),
            'sentiment_score': float(sentiment_score),
            'sentiment_adjusted_price': float(sentiment_adjusted_price),
            'final_prediction': float(final_prediction),
            'model_agreement': float(model_agreement),
            'sentiment_data': sentiment_data
        }
    
    def load_models(self, lstm_path: str, transformer_path: str):
        """Load trained models"""
        try:
            self.lstm_model.load(lstm_path)
            self.transformer_model.load(transformer_path)
        except Exception as e:
            print(f"Warning: Could not load models: {str(e)}")
            print("Models will need to be trained before making predictions")
    
    def save_models(self, lstm_path: str, transformer_path: str):
        """Save trained models"""
        self.lstm_model.save(lstm_path)
        self.transformer_model.save(transformer_path)
