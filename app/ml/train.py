import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

MODEL_PATH = os.path.join(os.path.dirname(__file__), "delay_model.pkl")
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "historical_delays.csv")


def train_delay_model():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Production dataset missing at {DATA_PATH}. Please provide a large-scale training dataset.")
    
    df = pd.read_csv(DATA_PATH)
    X = df[['distance', 'traffic_level']].values
    y = df['delay'].values
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Optimized RandomForestRegressor...")
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    predictions = model.predict(X_test)
    print("\n--- Model Evaluation Metrics ---")
    print(f"MSE: {mean_squared_error(y_test, predictions):.4f}")
    print(f"MAE: {mean_absolute_error(y_test, predictions):.4f}")
    print(f"R2 Score: {r2_score(y_test, predictions):.4f}\n")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    return model


def load_delay_model():
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    return train_delay_model()

if __name__ == "__main__":
    model = train_delay_model()
    print("Trained delay model and saved to", MODEL_PATH)
