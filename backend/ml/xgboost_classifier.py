import xgboost as xgb
import numpy as np

class XGBoostClassifier:
    """
    XGBoost model to classify market signals (Buy/Sell/Hold) based on indicators.
    """
    def __init__(self):
        self.model = xgb.XGBClassifier(
            objective='multi:softprob',
            num_class=3,
            eval_metric='mlogloss',
            use_label_encoder=False
        )

    def train(self, X_train, y_train):
        """
        Train the classifier.
        y_train: 0 (Sell), 1 (Hold), 2 (Buy)
        """
        self.model.fit(X_train, y_train)

    def predict_signal(self, features_row):
        """
        Predicts classes with confidence scores.
        """
        # features_row shape: (1, features_count)
        probs = self.model.predict_proba(features_row)[0]
        class_idx = np.argmax(probs)
        confidence = probs[class_idx]
        
        signal_map = {0: "SELL", 1: "HOLD", 2: "BUY"}
        return signal_map[class_idx], confidence

    def save(self, path="models/xgboost_signals.json"):
        self.model.save_model(path)
