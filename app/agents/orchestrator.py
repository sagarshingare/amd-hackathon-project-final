from app.agents.planner import PlannerAgent
from app.agents.optimizer import OptimizerAgent
from app.agents.disruption import DisruptionAgent
from app.agents.replanner import ReplanningAgent

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

    def run_disruption_and_replan(self, network):
        disruption = self.disruptor.apply(network)
        reoptimized = self.replanner.replan(network)

        return {
            "routes_after": reoptimized["routes"],
            "cost_after": reoptimized["total_cost"],
            "fuel_price_after": network["fuel_price"],
            "delay_multiplier": disruption["delay_multiplier"],
            "disruption_type": disruption["disruption_type"],
        }
