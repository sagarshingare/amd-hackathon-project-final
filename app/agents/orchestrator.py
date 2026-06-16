from app.agents.planner import PlannerAgent
from app.agents.optimizer import OptimizerAgent
from app.agents.disruption import DisruptionAgent
from app.agents.replanner import ReplanningAgent
import random

# Define production-level disruption scenarios as a module-level constant (PEP 8)
DISRUPTION_SCENARIOS = [
    {"type": "Accident on Route", "delay": 2.5, "fuel": 1.0, "desc": "Severe collision detected on primary road. Re-routing to avoid standstill traffic."},
    {"type": "Severe Weather", "delay": 1.8, "fuel": 1.1, "desc": "Heavy precipitation reducing visibility and speeds. Activating weather-safe routing."},
    {"type": "Road Block / Protest", "delay": 3.0, "fuel": 1.0, "desc": "Unexpected road closure. Completely avoiding downtown sector and rerouting outer perimeter."},
    {"type": "Fuel Price Spike", "delay": 1.0, "fuel": 1.5, "desc": "Sudden local fuel shortage detected. Optimizer prioritizing shortest distance over delivery time."}
]

class OrchestratorAgent:
    def __init__(self, predictor):
        self.planner = PlannerAgent()
        self.optimizer = OptimizerAgent(predictor=predictor)
        self.disruptor = DisruptionAgent()
        self.replanner = ReplanningAgent()

    def run_initial_optimization(self, network):
        plan = self.planner.plan_routes(network)
        optimized = self.optimizer.optimize(network)
        return {
            "routes_before": optimized["routes"],
            "routes_after": optimized["routes"],
            "cost_before": optimized["total_cost"],
            "cost_after": optimized["total_cost"],
            "fuel_price_before": network["fuel_price"],
            "fuel_price_after": network["fuel_price"],
            "delay_multiplier": network.get("delay_factor", 1.0),
            "disruption_type": None,
        }

    def run_disruption_and_replan(self, network, scenario_name=None):
        if scenario_name:
            scenario = next((s for s in DISRUPTION_SCENARIOS if s["type"] == scenario_name), random.choice(DISRUPTION_SCENARIOS))
        else:
            scenario = random.choice(DISRUPTION_SCENARIOS)
        
        # Apply the disruption modifiers directly to the network state
        network["delay_factor"] = network.get("delay_factor", 1.0) * scenario["delay"]
        network["fuel_price"] = network.get("fuel_price", 1.0) * scenario["fuel"]
        
        # Re-run optimization with the newly constrained network
        reoptimized = self.replanner.replan(network)

        return {
            "routes_after": reoptimized["routes"],
            "cost_after": reoptimized["total_cost"],
            "fuel_price_after": network["fuel_price"],
            "delay_multiplier": network["delay_factor"],
            "disruption_type": scenario["type"],
            "decision_details": scenario["desc"]
        }
