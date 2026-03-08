"""
Model training script
"""
import numpy as np
import argparse
from pathlib import Path

from backend.utils.data_fetcher import DataFetcher
from backend.utils.feature_engineering import FeatureEngineer
from backend.models.lstm_model import LSTMModel
from backend.models.transformer_model import TransformerModel
from backend.config import (
    LOOKBACK_WINDOW, EPOCHS, BATCH_SIZE, VALIDATION_SPLIT,
    LSTM_MODEL_FILE, TRANSFORMER_MODEL_FILE, SCALER_FILE
)
import joblib


def train_models(ticker: str = "AAPL", period: str = "2y"):
    """
    Train LSTM and Transformer models
    
    Args:
        ticker: Stock ticker to train on
        period: Historical period to use
    """
    print("\n" + "="*60)
    print(f"Training Models for {ticker}")
    print("="*60 + "\n")
    
    # Initialize components
    data_fetcher = DataFetcher()
    feature_engineer = FeatureEngineer()
    
    # Fetch data
    print("[*] Fetching stock data...")
    df = data_fetcher.fetch_stock_data(ticker, period=period)
    print(f"[+] Fetched {len(df)} days of data")
    
    # Prepare features
    print("\n[*] Engineering features...")
    df = feature_engineer.prepare_features(df)
    print(f"[+] Prepared {len(df)} samples with features")
    
    # Select features
    feature_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    # Scale data
    print("\n[*] Scaling data...")
    scaled_data = feature_engineer.scale_data(df, feature_columns)
    print("[+] Data scaled")
    
    # Create sequences
    print(f"\n[*] Creating sequences (lookback={LOOKBACK_WINDOW})...")
    X, y = feature_engineer.create_sequences(scaled_data, LOOKBACK_WINDOW)
    print(f"[+] Created {len(X)} sequences")
    
    # Split data
    split_idx = int(len(X) * (1 - VALIDATION_SPLIT))
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    print(f"\n[*] Data split:")
    print(f"  Training: {len(X_train)} samples")
    print(f"  Validation: {len(X_val)} samples")
    
    # Train LSTM model
    print(f"\n" + "="*60)
    print("Training LSTM Model")
    print("="*60 + "\n")
    
    lstm_model = LSTMModel(lookback=LOOKBACK_WINDOW, n_features=len(feature_columns))
    lstm_model.build_model()
    print(lstm_model.model.summary())
    
    print(f"\n[*] Training LSTM (epochs={EPOCHS}, batch_size={BATCH_SIZE})...")
    lstm_history = lstm_model.train(
        X_train, y_train,
        X_val, y_val,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE
    )
    
    # Save LSTM model
    print(f"\n[*] Saving LSTM model to {LSTM_MODEL_FILE}...")
    lstm_model.save(str(LSTM_MODEL_FILE))
    print("[+] LSTM model saved")
    
    # Train Transformer model
    print(f"\n" + "="*60)
    print("Training Transformer Model")
    print("="*60 + "\n")
    
    transformer_model = TransformerModel(lookback=LOOKBACK_WINDOW, n_features=len(feature_columns))
    transformer_model.build_model()
    print(transformer_model.model.summary())
    
    print(f"\n[*] Training Transformer (epochs={EPOCHS}, batch_size={BATCH_SIZE})...")
    transformer_history = transformer_model.train(
        X_train, y_train,
        X_val, y_val,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE
    )
    
    # Save Transformer model
    print(f"\n[*] Saving Transformer model to {TRANSFORMER_MODEL_FILE}...")
    transformer_model.save(str(TRANSFORMER_MODEL_FILE))
    print("[+] Transformer model saved")
    
    # Save scaler
    print(f"\n[*] Saving scaler to {SCALER_FILE}...")
    joblib.dump(feature_engineer.scaler, str(SCALER_FILE))
    print("[+] Scaler saved")
    
    # Print final metrics
    print(f"\n" + "="*60)
    print("Training Complete!")
    print("="*60 + "\n")
    
    print("[*] Final Metrics:")
    print(f"\nLSTM Model:")
    print(f"  Training Loss: {lstm_history['loss'][-1]:.6f}")
    print(f"  Validation Loss: {lstm_history['val_loss'][-1]:.6f}")
    
    print(f"\nTransformer Model:")
    print(f"  Training Loss: {transformer_history['loss'][-1]:.6f}")
    print(f"  Validation Loss: {transformer_history['val_loss'][-1]:.6f}")
    
    print(f"\n[+] Models ready for prediction!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train stock prediction models")
    parser.add_argument("--ticker", type=str, default="AAPL", help="Stock ticker symbol")
    parser.add_argument("--period", type=str, default="2y", help="Historical period (1y, 2y, 5y)")
    
    args = parser.parse_args()
    
    train_models(args.ticker, args.period)
