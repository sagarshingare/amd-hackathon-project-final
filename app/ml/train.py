import os
import pickle
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

MODEL_PATH = os.path.join(os.path.dirname(__file__), "delay_model.pkl")
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "historical_delays.csv")


def train_delay_model():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Production dataset missing at {DATA_PATH}. Please provide a large-scale training dataset.")
    
    df = pd.read_csv(DATA_PATH)
    X = df[['distance', 'traffic_level']].values
    y = df['delay'].values
    
    model = LinearRegression()
    model.fit(X, y)
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
