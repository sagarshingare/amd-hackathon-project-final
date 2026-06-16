import copy
from fastapi import APIRouter
from app.data.generate_data import generate_delivery_network
from app.agents.orchestrator import OrchestratorAgent
from app.ml.predict import DelayPredictor

router = APIRouter()

# Persist the current state for simulate flow
state = {
    "network": None,
    "baseline_network": None,
    "initial_result": None,
    "predictor": DelayPredictor(),
}

@router.post("/optimize")
def optimize():
    network = generate_delivery_network()
    state["network"] = network
    state["baseline_network"] = copy.deepcopy(network)

    orchestrator = OrchestratorAgent(predictor=state["predictor"])
    result = orchestrator.run_initial_optimization(network)
    state["initial_result"] = result

    return {
        "locations": network["locations"],
        "routes": result["routes_before"],
        "cost_before": result["cost_before"],
        "cost_after": result["cost_before"],
        "disruption": None,
        "summary": {
            "fleet_count": len(network["fleet"]),
            "order_count": len(network["orders"]),
            "fuel_price": network["fuel_price"],
        },
    }

@router.get("/simulate")
def simulate():
    if state["network"] is None:
        network = generate_delivery_network()
        state["network"] = network
        state["baseline_network"] = copy.deepcopy(network)
    else:
        network = state["network"]

    if state["initial_result"] is None:
        orchestrator = OrchestratorAgent(predictor=state["predictor"])
        state["initial_result"] = orchestrator.run_initial_optimization(network)

    orchestrator = OrchestratorAgent(predictor=state["predictor"])
    disruption_result = orchestrator.run_disruption_and_replan(network)
    state["network"] = network

    return {
        "locations": state["baseline_network"]["locations"],
        "routes_before": state["initial_result"]["routes_before"],
        "routes_after": disruption_result["routes_after"],
        "cost_before": state["initial_result"]["cost_before"],
        "cost_after": disruption_result["cost_after"],
        "disruption": disruption_result["disruption_type"],
        "summary": {
            "fuel_price_before": state["baseline_network"]["fuel_price"],
            "fuel_price_after": disruption_result["fuel_price_after"],
            "delay_multiplier": disruption_result["delay_multiplier"],
        },
    }
