"""
Transformer-based time series prediction model
"""
import keras
from keras import layers, Model
import numpy as np
from typing import Tuple


class PositionalEncoding(layers.Layer):
    """Positional encoding for transformer"""
    
    def __init__(self, max_len: int = 100, d_model: int = 64, **kwargs):
        super(PositionalEncoding, self).__init__(**kwargs)
        self.max_len = max_len
        self.d_model = d_model
    
    def build(self, input_shape):
        # Create positional encoding matrix
        position = np.arange(self.max_len)[:, np.newaxis]
        div_term = np.exp(np.arange(0, self.d_model, 2) * -(np.log(10000.0) / self.d_model))
        
        pos_encoding = np.zeros((self.max_len, self.d_model))
        pos_encoding[:, 0::2] = np.sin(position * div_term)
        pos_encoding[:, 1::2] = np.cos(position * div_term)
        
        import keras.ops as ops
        self.pos_encoding = ops.convert_to_tensor(pos_encoding, dtype='float32')
        super(PositionalEncoding, self).build(input_shape)
    
    def call(self, inputs):
        import keras.ops as ops
        seq_len = ops.shape(inputs)[1]
        return inputs + self.pos_encoding[:seq_len, :]
    
    def get_config(self):
        config = super(PositionalEncoding, self).get_config()
        config.update({
            'max_len': self.max_len,
            'd_model': self.d_model
        })
        return config


class TransformerBlock(layers.Layer):
    """Transformer encoder block"""
    
    def __init__(self, d_model: int, num_heads: int, ff_dim: int, dropout: float = 0.1, **kwargs):
        super(TransformerBlock, self).__init__(**kwargs)
        self.d_model = d_model
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.dropout_rate = dropout
        
        self.att = layers.MultiHeadAttention(num_heads=num_heads, key_dim=d_model)
        self.ffn = keras.Sequential([
            layers.Dense(ff_dim, activation='relu'),
            layers.Dense(d_model)
        ])
        
        self.layernorm1 = layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = layers.LayerNormalization(epsilon=1e-6)
        self.dropout1 = layers.Dropout(dropout)
        self.dropout2 = layers.Dropout(dropout)
    
    def call(self, inputs, training=False):
        # Multi-head attention
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        
        # Feed-forward network
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)
    
    def get_config(self):
        config = super(TransformerBlock, self).get_config()
        config.update({
            'd_model': self.d_model,
            'num_heads': self.num_heads,
            'ff_dim': self.ff_dim,
            'dropout': self.dropout_rate
        })
        return config


class TransformerModel:
    """Transformer-based time series prediction model"""
    
    def __init__(self, lookback: int = 60, n_features: int = 5):
        """
        Initialize Transformer model
        
        Args:
            lookback: Number of time steps to look back
            n_features: Number of input features
        """
        self.lookback = lookback
        self.n_features = n_features
        self.model = None
        self.d_model = 64
    
    def build_model(self) -> Model:
        """
        Build Transformer model
        
        Returns:
            Compiled Keras model
        """
        inputs = keras.Input(shape=(self.lookback, self.n_features))
        
        # Project input features to d_model dimensions
        x = layers.Dense(self.d_model)(inputs)
        
        # Add positional encoding
        x = PositionalEncoding(max_len=self.lookback, d_model=self.d_model)(x)
        
        # Transformer encoder blocks
        x = TransformerBlock(d_model=self.d_model, num_heads=4, ff_dim=128, dropout=0.1)(x)
        x = TransformerBlock(d_model=self.d_model, num_heads=4, ff_dim=128, dropout=0.1)(x)
        x = TransformerBlock(d_model=self.d_model, num_heads=4, ff_dim=128, dropout=0.1)(x)
        
        # Global average pooling
        x = layers.GlobalAveragePooling1D()(x)
        
        # Dense layers
        x = layers.Dense(64, activation='relu')(x)
        x = layers.Dropout(0.2)(x)
        x = layers.Dense(32, activation='relu')(x)
        x = layers.Dropout(0.2)(x)
        
        # Output layer
        outputs = layers.Dense(1)(x)
        
        # Create model
        model = Model(inputs=inputs, outputs=outputs, name='Transformer_TimeSeries')
        
        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
        return model
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray = None, y_val: np.ndarray = None,
              epochs: int = 50, batch_size: int = 32) -> dict:
        """
        Train the Transformer model
        
        Args:
            X_train: Training sequences
            y_train: Training targets
            X_val: Validation sequences
            y_val: Validation targets
            epochs: Number of training epochs
            batch_size: Batch size
            
        Returns:
            Training history
        """
        if self.model is None:
            self.build_model()
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss' if X_val is not None else 'loss',
                patience=10,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss' if X_val is not None else 'loss',
                factor=0.5,
                patience=5,
                min_lr=0.00001
            )
        ]
        
        # Train model
        validation_data = (X_val, y_val) if X_val is not None else None
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        return history.history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions
        
        Args:
            X: Input sequences
            
        Returns:
            Predictions
        """
        if self.model is None:
            raise ValueError("Model not built or loaded")
        
        return self.model.predict(X, verbose=0)
    
    def save(self, filepath: str):
        """Save model to file"""
        if self.model is not None:
            self.model.save(filepath)
    
    def load(self, filepath: str):
        """Load model from file"""
        self.model = keras.models.load_model(
            filepath,
            custom_objects={
                'PositionalEncoding': PositionalEncoding,
                'TransformerBlock': TransformerBlock
            }
        )
