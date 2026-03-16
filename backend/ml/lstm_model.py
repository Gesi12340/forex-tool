try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    HAS_TF = True
except ImportError:
    HAS_TF = False

class LSTMModel:
    """
    LSTM model for time-series forecasting of Forex price movements.
    """
    def __init__(self, sequence_length=60, features_count=5):
        self.sequence_length = sequence_length
        self.features_count = features_count
        if HAS_TF:
            self.model = self._build_model()
        else:
            print("WARNING: TensorFlow not found. Using Mock LSTM predictions.")
            self.model = None

    def _build_model(self):
        if not HAS_TF: return None
        model = Sequential([
            LSTM(units=50, return_sequences=True, input_shape=(self.sequence_length, self.features_count)),
            Dropout(0.2),
            LSTM(units=50, return_sequences=False),
            Dropout(0.2),
            Dense(units=25),
            Dense(units=1)  # Predict next close price
        ])
        model.compile(optimizer='adam', loss='mean_squared_error')
        return model

    def train_on_batch(self, X_train, y_train):
        """Train model on a historical data batch."""
        self.model.fit(X_train, y_train, batch_size=32, epochs=10)

    def predict_next(self, sequence):
        """Predicts the next price point based on the provided sequence."""
        if not HAS_TF or self.model is None:
            # Return a slight variation of the last price in the sequence
            return sequence[0, -1, 0] * 1.0001 
        # sequence shape: (1, sequence_length, features_count)
        return self.model.predict(sequence)[0][0]

    def save(self, path="models/lstm_forex.h5"):
        self.model.save(path)
