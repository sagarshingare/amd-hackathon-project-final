import os
import pickle
import numpy as np
from app.ml.train import load_delay_model
from app.data.real_data import generate_distance_matrix

MODEL_PATH = os.path.join(os.path.dirname(__file__), "delay_model.pkl")

class DelayPredictor:
    def __init__(self):
        self.model = load_delay_model()

    def predict_delays(self, network):
        distance_matrix = generate_distance_matrix(network["locations"])
        delays = [0.0] * len(network["locations"])
        for idx in range(1, len(network["locations"])):
            distance = distance_matrix[0][idx]
            traffic_level = network.get("delay_factor", 1.0)
            features = np.array([[distance, traffic_level]])
            delay = self.model.predict(features)[0]
            delays[idx] = max(0.0, float(delay))
        network["predicted_delays"] = delays
        return delays
