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
            predicted_delays=predicted_delays,
        )
        return solver_result
