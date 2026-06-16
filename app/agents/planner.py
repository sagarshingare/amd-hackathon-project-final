from app.data.real_data import generate_distance_matrix

class PlannerAgent:
    def plan_routes(self, network):
        locations = network["locations"]
        distance_matrix = generate_distance_matrix(locations)
        return {
            "locations": locations,
            "orders": network["orders"],
            "fleet": network["fleet"],
            "distance_matrix": distance_matrix,
            "fuel_price": network["fuel_price"],
        }
