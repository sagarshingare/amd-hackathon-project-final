import os
import pickle
import numpy as np
from app.ml.train import load_delay_model

MODEL_PATH = os.path.join(os.path.dirname(__file__), "delay_model.pkl")

class DelayPredictor:
    def __init__(self):
        self.model = load_delay_model()

    def predict_delays(self, network):
        # The distance matrix from the network is in centimiles.
        distance_matrix_centi = network.get("distance_matrix")
        if distance_matrix_centi is None:
            from app.optimization.vrp_solver import build_distance_matrix
            distance_matrix_centi = build_distance_matrix(network["locations"])
        
        num_locations = len(network["locations"])
        # Create a matrix for predicted delays between any two nodes
        delay_matrix = [[0.0] * num_locations for _ in range(num_locations)]
        traffic_level = network.get("delay_factor", 1.0)

        for i in range(num_locations):
            for j in range(num_locations):
                if i == j:
                    continue
                distance = distance_matrix_centi[i][j] / 100.0
                features = np.array([[distance, traffic_level]])
                delay = self.model.predict(features)[0]
                delay_matrix[i][j] = max(0.0, float(delay))

        network["predicted_delays"] = delay_matrix # Now it's a matrix
        return delay_matrix
