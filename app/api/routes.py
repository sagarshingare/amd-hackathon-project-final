import copy
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.data.real_data import generate_delivery_network
from app.agents.orchestrator import OrchestratorAgent
from app.ml.predict import DelayPredictor
from app.session import create_session, save_state, load_state

router = APIRouter()

class OptimizeRequest(BaseModel):
    num_vehicles: int = 3
    vehicle_capacity: int = 150
    fuel_price: float = 1.0
    driver_hourly_wage: float = 25.0
    num_orders: int = 10
    source: str = "NYC"


def format_routes(routes_indices, locations):
    formatted = []
    for route in routes_indices:
        coords = [locations[idx] for idx in route]
        formatted.append({"route": route, "coords": coords})
    return formatted


@router.post("/optimize")
def optimize(req: OptimizeRequest):
    session_id = create_session()
    predictor = DelayPredictor()

    network = generate_delivery_network(source=req.source, num_orders=req.num_orders)
    
    network["fleet"] = [{"vehicle_id": f"V{i}", "capacity": req.vehicle_capacity, "type": "truck"} for i in range(req.num_vehicles)]
    network["fuel_price"] = req.fuel_price
    network["driver_cost_per_minute"] = req.driver_hourly_wage / 60.0
    
    orchestrator = OrchestratorAgent(predictor=predictor)
    result = orchestrator.run_initial_optimization(network)
    
    # Save the initial state for the simulation step
    state_to_save = {
        "baseline_network": copy.deepcopy(network),
        "initial_result": result,
    }
    save_state(session_id, state_to_save)

    return {
        "session_id": session_id,
        "locations": network["locations"],
        "depot_time_window": network.get("depot_time_window"),
        "routes": format_routes(result["cost_before"]["routes"], network["locations"]),
        "cost_before": result["cost_before"],
        "cost_after": result["cost_after"],
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
def simulate(session_id: str, scenario: Optional[str] = None):
    state = load_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired. Please run initial optimization again.")

    # Use a deep copy to avoid modifying the original baseline state
    network_for_disruption = copy.deepcopy(state["baseline_network"])

    predictor = DelayPredictor()
    orchestrator = OrchestratorAgent(predictor=predictor)
    disruption_result = orchestrator.run_disruption_and_replan(network_for_disruption, scenario_name=scenario)

    # No need to save state again unless we want a multi-step simulation

    return {
        "locations": state["baseline_network"]["locations"],
        "depot_time_window": state["baseline_network"].get("depot_time_window"),
        "routes_before": format_routes(state["initial_result"]["routes_before"], state["baseline_network"]["locations"]),
        "routes_after": format_routes(disruption_result["cost_after"]["routes"], state["baseline_network"]["locations"]),
        "cost_before": state["initial_result"]["cost_before"],
        "cost_after": disruption_result["cost_after"],
        "disruption": disruption_result["disruption_type"],
        "decision_details": disruption_result.get("decision_details", ""),
        "summary": {
            "fuel_price_before": state["baseline_network"]["fuel_price"],
            "fuel_price_after": disruption_result["fuel_price_after"],
            "delay_multiplier": disruption_result["delay_multiplier"],
            "city": state["baseline_network"].get("city", "Unknown"),
        },
        "orders": state["baseline_network"]["orders"],
    }
