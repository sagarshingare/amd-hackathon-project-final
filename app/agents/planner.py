from app.optimization.vrp_solver import build_distance_matrix

class PlannerAgent:
    def plan_routes(self, network):
        locations = network["locations"]
        distance_matrix = build_distance_matrix(locations)
        return {
            "locations": locations,
            "orders": network["orders"],
            "fleet": network["fleet"],
            "distance_matrix": distance_matrix,
            "fuel_price": network["fuel_price"],
        }
