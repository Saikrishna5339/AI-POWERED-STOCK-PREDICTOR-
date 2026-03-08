"""
Trading signal generator
"""
from typing import Dict
from backend.config import STRONG_BUY_THRESHOLD, STRONG_SELL_THRESHOLD


class SignalGenerator:
    """Generates trading signals based on predictions"""
    
    def __init__(self):
        self.strong_buy_threshold = STRONG_BUY_THRESHOLD
        self.strong_sell_threshold = STRONG_SELL_THRESHOLD
    
    def generate_signal(self, prediction_data: Dict) -> Dict:
        """
        Generate trading signal
        
        Args:
            prediction_data: Dictionary with prediction results
            
        Returns:
            Dictionary with signal and reasoning
        """
        current_price = prediction_data['current_price']
        final_prediction = prediction_data['final_prediction']
        sentiment_score = prediction_data['sentiment_score']
        
        # Calculate price change ratio
        price_ratio = final_prediction / current_price
        
        # Determine sentiment category
        is_positive_sentiment = sentiment_score > 0.1
        is_negative_sentiment = sentiment_score < -0.1
        
        # Generate signal based on logic
        if price_ratio > self.strong_buy_threshold and is_positive_sentiment:
            signal = "STRONG BUY"
            color = "#00ff00"
            reasoning = f"Predicted price ${final_prediction:.2f} is {((price_ratio-1)*100):.2f}% higher than current ${current_price:.2f} with positive sentiment"
        elif price_ratio > 1.0:
            signal = "BUY"
            color = "#90EE90"
            reasoning = f"Predicted price ${final_prediction:.2f} is {((price_ratio-1)*100):.2f}% higher than current ${current_price:.2f}"
        elif price_ratio < self.strong_sell_threshold and is_negative_sentiment:
            signal = "STRONG SELL"
            color = "#ff0000"
            reasoning = f"Predicted price ${final_prediction:.2f} is {((1-price_ratio)*100):.2f}% lower than current ${current_price:.2f} with negative sentiment"
        elif price_ratio < 1.0:
            signal = "SELL"
            color = "#FFB6C1"
            reasoning = f"Predicted price ${final_prediction:.2f} is {((1-price_ratio)*100):.2f}% lower than current ${current_price:.2f}"
        else:
            signal = "HOLD"
            color = "#FFD700"
            reasoning = f"Predicted price ${final_prediction:.2f} is close to current ${current_price:.2f}"
        
        return {
            'signal': signal,
            'color': color,
            'reasoning': reasoning,
            'price_change_percent': float((price_ratio - 1) * 100)
        }
