import os
import pickle
import random
import numpy as np
from sklearn.linear_model import LinearRegression
from app.data.generate_data import generate_distance_matrix

MODEL_PATH = os.path.join(os.path.dirname(__file__), "delay_model.pkl")


def build_synthetic_dataset(samples=200):
    X = []
    y = []
    for _ in range(samples):
        distance = random.uniform(1.0, 100.0)
        traffic_level = random.uniform(0.8, 1.8)
        base_delay = distance * 0.05
        delay = base_delay * traffic_level + random.uniform(0.0, 2.0)
        X.append([distance, traffic_level])
        y.append(delay)
    return np.array(X), np.array(y)


def train_delay_model():
    X, y = build_synthetic_dataset()
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
