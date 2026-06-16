from app.optimization.vrp_solver import solve_vrp

class ReplanningAgent:
    def replan(self, network):
        return solve_vrp(
            locations=network["locations"],
            orders=network["orders"],
            fleet=network["fleet"],
            fuel_price=network["fuel_price"],
            predicted_delays=network.get("predicted_delays", None),
        )
