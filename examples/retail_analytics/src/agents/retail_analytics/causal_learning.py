import os
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from typing import Dict, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score
import logging

logger = logging.getLogger(__name__)

class CausalLearner:
    """
    Machine Learning component for Causal Analysis.
    Predicts 'Impact Score' and 'Probability of Disruption' based on weather features.
    """
    
    def __init__(self, data_path: Optional[str] = None, model_dir: Optional[str] = None):
        example_root = Path(__file__).resolve().parents[3]
        data_path = Path(data_path or "data/real_causal_data.csv")
        model_dir = Path(model_dir or "models")
        self.data_path = str(data_path if data_path.is_absolute() else example_root / data_path)
        self.model_dir = str(model_dir if model_dir.is_absolute() else example_root / model_dir)
        self.impact_model_path = os.path.join(self.model_dir, "causal_impact_regressor.pkl")
        self.prob_model_path = os.path.join(self.model_dir, "causal_prob_classifier.pkl")
        
        self.impact_model = None
        self.prob_model = None
        self.is_trained = False
        
        os.makedirs(self.model_dir, exist_ok=True)
        
    def load_models(self) -> bool:
        """Load pre-trained models from disk."""
        if os.path.exists(self.impact_model_path) and os.path.exists(self.prob_model_path):
            try:
                self.impact_model = joblib.load(self.impact_model_path)
                self.prob_model = joblib.load(self.prob_model_path)
                self.is_trained = True
                logger.info("Causal ML models loaded successfully.")
                return True
            except Exception as e:
                logger.error(f"Failed to load models: {e}")
                return False
        return False

    def train(self) -> Dict[str, float]:
        """Train models using the generated real dataset."""
        if not os.path.exists(self.data_path):
            logger.error(f"Training data not found at {self.data_path}")
            return {"status": "error", "message": "Dataset missing"}
            
        try:
            df = pd.read_csv(self.data_path)
            
            # Features: Weather metrics
            X = df[["max_temp", "min_temp", "avg_temp", "total_rain", "max_wind", "avg_humidity"]]
            
            # Targets
            y_impact = df["impact_score"]
            # To train a classifier for probability, we can treat probability > 0.5 as "Disruption" class
            # Or we can just regress the probability value directly using a regressor. 
            # Regressor is better for continuous 0.0-1.0 probability output.
            y_prob = df["prob_disruption"]
            
            # Train Impact Regressor
            self.impact_model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.impact_model.fit(X, y_impact)
            
            # Train Probability Regressor (predicting the probability score directly)
            self.prob_model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.prob_model.fit(X, y_prob)
            
            # Save models
            joblib.dump(self.impact_model, self.impact_model_path)
            joblib.dump(self.prob_model, self.prob_model_path)
            self.is_trained = True
            
            logger.info("Causal ML models trained and saved.")
            return {"status": "success", "message": "Models trained"}
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {"status": "error", "message": str(e)}

    def predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """
        Predict Impact Score and Probability for a live event.
        features: dict with keys [max_temp, min_temp, total_rain, max_wind, avg_humidity]
        (avg_temp inferred if missing)
        """
        if not self.is_trained:
            if not self.load_models():
                logger.warning("Models not trained/loaded. Returning default heuristics.")
                return self._heuristic_fallback(features)
        
        try:
            # Prepare input vector (handle missing optional fields)
            max_temp = features.get("max_temp", 25.0)
            min_temp = features.get("min_temp", 15.0)
            avg_temp = features.get("avg_temp", (max_temp + min_temp)/2)
            total_rain = features.get("total_rain", 0.0)
            max_wind = features.get("max_wind", 10.0)
            avg_hum = features.get("avg_humidity", 50.0)
            
            X_input = pd.DataFrame([[max_temp, min_temp, avg_temp, total_rain, max_wind, avg_hum]], 
                                   columns=["max_temp", "min_temp", "avg_temp", "total_rain", "max_wind", "avg_humidity"])
            
            pred_impact = self.impact_model.predict(X_input)[0]
            pred_prob = self.prob_model.predict(X_input)[0]
            
            # Clamp values
            pred_impact = max(1.0, min(10.0, float(pred_impact)))
            pred_prob = max(0.0, min(1.0, float(pred_prob)))
            
            return pred_impact, pred_prob
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return self._heuristic_fallback(features)

    def _heuristic_fallback(self, features) -> Tuple[float, float]:
        """Simple rule-based fallback if ML fails."""
        score = 1.0
        if features.get("max_wind", 0) > 80: score += 5
        if features.get("total_rain", 0) > 50: score += 3
        return min(10.0, score), 0.5
