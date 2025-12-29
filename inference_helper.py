import joblib
import pandas as pd
import numpy as np
import os
import xgboost as xgb

class FlightDelayPredictor:
    def __init__(self, artifacts_dir='artifacts'):
        self.artifacts_dir = artifacts_dir
        self.model = None
        self.global_mean = None
        self.risk_maps = {}
        self.features_finales = [
            'MONTH_SIN', 'MONTH_COS', 'DAY_SIN', 'DAY_COS',
            'DISTANCE_GROUP', 'SEGMENT_NUMBER', 'CONCURRENT_FLIGHTS',
            'PRCP', 'TMAX', 'AWND', 'SNOW', 'SNWD', 'PLANE_AGE',
            'AIRPORT_FLIGHTS_MONTH', 'CARRIER_NAME_RISK',
            'DEPARTING_AIRPORT_RISK', 'DEP_TIME_BLK_RISK'
        ]

    def load_artifacts(self):
        """Loads the model and necessary artifacts."""
        try:
            print(f"Loading artifacts from {self.artifacts_dir}...")
            self.model = joblib.load(os.path.join(self.artifacts_dir, 'flight_delay_xgb.joblib'))
            self.global_mean = joblib.load(os.path.join(self.artifacts_dir, 'global_mean_improved.joblib'))

            for col in ['CARRIER_NAME', 'DEPARTING_AIRPORT', 'DEP_TIME_BLK']:
                self.risk_maps[col] = joblib.load(os.path.join(self.artifacts_dir, f'{col}_risk_map_improved.joblib'))
            print("Artifacts loaded successfully.")
            return True
        except Exception as e:
            print(f"Error loading artifacts: {e}")
            return False

    def preprocess_input(self, input_data):
        """
        Preprocesses a single input dictionary or dataframe row.

        Expected input keys (matching the hackathon contract + internal features):
        - aerolinea (Mapped to CARRIER_NAME)
        - origen (Mapped to DEPARTING_AIRPORT)
        - fecha_partida (To extract MONTH, DAY_OF_WEEK, DEP_TIME_BLK)
        - distancia_km (To calculate DISTANCE_GROUP)

        Note: For the additional features required by the improved model (Weather, Traffic),
        this MVP inference helper will use DEFAULT/MEAN values if not provided.
        In a real production system, these would be fetched from external APIs.
        """

        # 1. Parse Date
        try:
            dt = pd.to_datetime(input_data['fecha_partida'])
            month = dt.month
            day_of_week = dt.dayofweek + 1 # Monday=1, Sunday=7
            hour = dt.hour

            # Construct DEP_TIME_BLK (e.g., "1400-1459")
            dep_time_blk = f"{hour:02d}00-{hour:02d}59"

        except Exception as e:
            print(f"Error parsing date: {e}")
            return None

        # 2. Map Contract Keys to Model Features
        # Distance Group (Every 250 miles approx, simplified logic here)
        # 1 mile = 1.60934 km
        distance_miles = input_data.get('distancia_km', 0) / 1.60934
        distance_group = min(max(int(distance_miles // 250) + 1, 1), 11)

        # 3. Create Feature Vector
        features = {}

        # Cyclic Encoding
        features['MONTH_SIN'] = np.sin(2 * np.pi * month / 12)
        features['MONTH_COS'] = np.cos(2 * np.pi * month / 12)
        features['DAY_SIN'] = np.sin(2 * np.pi * day_of_week / 7)
        features['DAY_COS'] = np.cos(2 * np.pi * day_of_week / 7)

        features['DISTANCE_GROUP'] = distance_group

        # --- MISSING DATA IMPUTATION (MVP Strategy) ---
        # Since the input contract doesn't have these, we use defaults/means
        # based on typical values to allow the model to run.
        features['SEGMENT_NUMBER'] = input_data.get('segment_number', 1)
        features['CONCURRENT_FLIGHTS'] = input_data.get('concurrent_flights', 20) # Median value guess
        features['PRCP'] = input_data.get('prcp', 0.0) # Assume no rain if unknown
        features['TMAX'] = input_data.get('tmax', 20.0) # Mild temp
        features['AWND'] = input_data.get('awnd', 5.0) # Light wind
        features['SNOW'] = input_data.get('snow', 0.0) # No snow
        features['SNWD'] = input_data.get('snwd', 0.0) # No snow depth
        features['PLANE_AGE'] = input_data.get('plane_age', 5) # Median age
        features['AIRPORT_FLIGHTS_MONTH'] = input_data.get('airport_flights_month', 1000)

        # Target Encoding (Risk Mapping)
        carrier = input_data.get('aerolinea', 'UNKNOWN')
        origin = input_data.get('origen', 'UNKNOWN')

        features['CARRIER_NAME_RISK'] = self.risk_maps['CARRIER_NAME'].get(carrier, self.global_mean)
        features['DEPARTING_AIRPORT_RISK'] = self.risk_maps['DEPARTING_AIRPORT'].get(origin, self.global_mean)
        features['DEP_TIME_BLK_RISK'] = self.risk_maps['DEP_TIME_BLK'].get(dep_time_blk, self.global_mean)

        # Convert to DataFrame with correct column order
        return pd.DataFrame([features], columns=self.features_finales)

    def predict(self, input_data):
        if self.model is None:
            if not self.load_artifacts():
                return {"error": "Model not loaded"}

        df_features = self.preprocess_input(input_data)

        if df_features is None:
             return {"error": "Preprocessing failed"}

        # Predict
        try:
            # XGBoost binary classification
            prediction = self.model.predict(df_features)[0]
            probability = self.model.predict_proba(df_features)[0][1]

            result = {
                "prevision": "Retrasado" if prediction == 1 else "Puntual",
                "probabilidad": float(round(probability, 2))
            }
            return result
        except Exception as e:
            return {"error": f"Prediction failed: {e}"}

# Example Usage
if __name__ == "__main__":
    predictor = FlightDelayPredictor()

    # Test with the example from the prompt
    sample_input = {
        "aerolinea": "AZ",
        "origen": "GIG",
        "destino": "GRU",
        "fecha_partida": "2025-11-10T14:30:00",
        "distancia_km": 350
    }

    print("Testing Prediction with Sample Input:")
    print(predictor.predict(sample_input))
