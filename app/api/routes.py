import copy
from fastapi import APIRouter
from app.data.real_data import generate_delivery_network
from app.agents.orchestrator import OrchestratorAgent
from app.ml.predict import DelayPredictor

router = APIRouter()

# Persist the current state for simulate flow
state = {
    "network": None,
    "baseline_network": None,
    "initial_result": None,
    "predictor": DelayPredictor(),
    "data_source": "NYC",
}

def format_routes(routes_indices, locations):
    formatted = []
    for route in routes_indices:
        coords = [locations[idx] for idx in route]
        formatted.append({"route": route, "coords": coords})
    return formatted

@router.post("/optimize")
def optimize(source: str = "NYC"):
    network = generate_delivery_network(source=source, num_orders=10)
    state["network"] = network
    state["baseline_network"] = copy.deepcopy(network)
    state["data_source"] = source

    orchestrator = OrchestratorAgent(predictor=state["predictor"])
    result = orchestrator.run_initial_optimization(network)
    state["initial_result"] = result

    return {
        "locations": network["locations"],
        "routes": format_routes(result["routes_before"], network["locations"]),
        "cost_before": result["cost_before"],
        "cost_after": result["cost_before"],
        "disruption": None,
        "summary": {
            "fleet_count": len(network["fleet"]),
            "order_count": len(network["orders"]),
            "fuel_price": network["fuel_price"],
            "city": network.get("city", "Unknown"),
            "dataset_source": network.get("dataset_source", ""),
        },
        "orders": network["orders"],
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
        "routes_before": format_routes(state["initial_result"]["routes_before"], state["baseline_network"]["locations"]),
        "routes_after": format_routes(disruption_result["routes_after"], state["baseline_network"]["locations"]),
        "cost_before": state["initial_result"]["cost_before"],
        "cost_after": disruption_result["cost_after"],
        "disruption": disruption_result["disruption_type"],
        "summary": {
            "fuel_price_before": state["baseline_network"]["fuel_price"],
            "fuel_price_after": disruption_result["fuel_price_after"],
            "delay_multiplier": disruption_result["delay_multiplier"],
            "city": state["baseline_network"].get("city", "Unknown"),
        },
        "orders": state["baseline_network"]["orders"],
    }
