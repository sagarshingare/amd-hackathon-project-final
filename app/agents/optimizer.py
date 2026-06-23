from app.optimization.vrp_solver import solve_vrp
from app.ml.predict import DelayPredictor

class OptimizerAgent:
    def __init__(self, predictor: DelayPredictor):
        self.predictor = predictor

    def optimize(self, network, disruption=None):
        predicted_delays = self.predictor.predict_delays(network)
        solver_result = solve_vrp(
            locations=network["locations"],
            orders=network["orders"],
            fleet=network["fleet"],
            fuel_price=network["fuel_price"],
            driver_cost_per_minute=network.get("driver_cost_per_minute", 0.42),
            predicted_delays=predicted_delays,
            distance_matrix=network.get("distance_matrix"),
            depot_time_window=network.get("depot_time_window", (0, 1440))
        )
        return solver_result
