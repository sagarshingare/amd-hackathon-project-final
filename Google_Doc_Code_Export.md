# Project Folder Structure and Code

## Folder Structure

Click on any file name to jump to its contents.

* 📁 **app/**
  * 📁 **agents/**
    * 📄 [__init__.py](#appagentsinitpy)
    * 📄 [disruption.py](#appagentsdisruptionpy)
    * 📄 [optimizer.py](#appagentsoptimizerpy)
    * 📄 [orchestrator.py](#appagentsorchestratorpy)
    * 📄 [planner.py](#appagentsplannerpy)
    * 📄 [replanner.py](#appagentsreplannerpy)
  * 📁 **api/**
    * 📄 [routes.py](#appapiroutespy)
  * 📁 **data/**
    * 📄 [__init__.py](#appdatainitpy)
    * 📄 [generate_data.py](#appdatageneratedatapy)
    * 📄 [real_data.py](#appdatarealdatapy)
    * 📄 sample_submission.zip *(binary/excluded)*
    * 📄 test.zip *(binary/excluded)*
    * 📄 train.zip *(binary/excluded)*
  * 📁 **ml/**
    * 📄 [__init__.py](#appmlinitpy)
    * 📄 delay_model.pkl *(binary/excluded)*
    * 📄 [predict.py](#appmlpredictpy)
    * 📄 [train.py](#appmltrainpy)
  * 📁 **optimization/**
    * 📄 [__init__.py](#appoptimizationinitpy)
    * 📄 [vrp_solver.py](#appoptimizationvrpsolverpy)
  * 📁 **utils/**
    * 📄 [__init__.py](#apputilsinitpy)
    * 📄 [cost.py](#apputilscostpy)
    * 📄 [features.py](#apputilsfeaturespy)
  * 📄 [__init__.py](#appinitpy)
  * 📄 [main.py](#appmainpy)
  * 📄 [session.py](#appsessionpy)
* 📁 **data/**
  * 📄 [deliveries.csv](#datadeliveriescsv)
  * 📄 [historical_delays.csv](#datahistoricaldelayscsv)
* 📁 **frontend/**
  * 📄 [app.py](#frontendapppy)
* 📄 [README.md](#readmemd)
* 📄 [download_kaggle_data.py](#downloadkaggledatapy)
* 📄 [requirements.txt](#requirementstxt)

---

## File Contents

<a id="readmemd"></a>
### 📄 README.md

```markdown
# Agentic AI Logistics Optimization

A production-ready open-source agentic AI system for logistics route optimization, disruption simulation, and real-time rerouting.

## Features

- Multi-vehicle routing with OR-Tools
- Cost optimization for distance, fuel, and delay
- Disruption simulation for traffic and fuel spikes
- ML training pipeline for travel delay prediction
- Streamlit frontend with route plots and cost comparison
- FastAPI backend with `/optimize` and `/simulate`

## Project Structure

```text
app/
├── __init__.py
├── main.py
├── api/
│   └── routes.py
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── planner.py
│   ├── optimizer.py
│   └── replanner.py
├── data/
│   └── real_data.py
├── ml/
│   ├── __init__.py
│   ├── train.py
│   └── predict.py
├── optimization/
│   └── vrp_solver.py
└── session.py
frontend/
└── app.py
requirements.txt
README.md
```

## Run Instructions

1. Create and activate a Python environment.
2. Install dependencies:

```bash
cd /Users/sagarshingare/Documents/amd-hackathon-project-final
python3 -m pip install -r requirements.txt
```

3. Start the backend API:

```bash
cd /Users/sagarshingare/Documents/amd-hackathon-project-final
PYTHONPATH=. python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

4. Start the Streamlit frontend:

```bash
cd /Users/sagarshingare/Documents/amd-hackathon-project-final # Use python -m streamlit for robust pathing
python3 -m streamlit run frontend/app.py
```

## Demo Flow

1. Generate delivery network
2. Run initial optimization
3. Show routes + cost
4. Trigger disruption (fuel or traffic)
5. Rerun optimization
6. Show updated routes + cost difference

## API Examples

```bash
curl -X POST "http://127.0.0.1:8000/optimize"
curl "http://127.0.0.1:8000/simulate"
```

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appinitpy"></a>
### 📄 app/__init__.py

```python
# (Empty file)

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appagentsinitpy"></a>
### 📄 app/agents/__init__.py

```python
# (Empty file)

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appagentsdisruptionpy"></a>
### 📄 app/agents/disruption.py

```python
import random

class DisruptionAgent:
    def __init__(self):
        self.disruption_type = None
        self.delay_multiplier = 1.0
        self.fuel_multiplier = 1.0

    def simulate(self):
        self.disruption_type = random.choice(["traffic_delay", "fuel_spike"])
        if self.disruption_type == "traffic_delay":
            self.delay_multiplier = random.uniform(1.2, 1.8)
            self.fuel_multiplier = 1.0
        else:
            self.fuel_multiplier = random.uniform(1.15, 1.35)
            self.delay_multiplier = 1.0

        return {
            "disruption_type": self.disruption_type,
            "delay_multiplier": self.delay_multiplier,
            "fuel_multiplier": self.fuel_multiplier,
        }

    def apply(self, network):
        disruption = self.simulate()
        if disruption["disruption_type"] == "fuel_spike":
            network["fuel_price"] *= disruption["fuel_multiplier"]
        else:
            network["delay_factor"] = disruption["delay_multiplier"]
        return disruption

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appagentsoptimizerpy"></a>
### 📄 app/agents/optimizer.py

```python
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

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appagentsorchestratorpy"></a>
### 📄 app/agents/orchestrator.py

```python
from app.agents.planner import PlannerAgent
from app.agents.optimizer import OptimizerAgent
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
        self.replanner = ReplanningAgent(predictor=predictor)

    def run_initial_optimization(self, network):
        plan = self.planner.plan_routes(network)
        optimized = self.optimizer.optimize(network)
        return {
            "routes_before": optimized["routes"],
            "cost_before": optimized, # Return the full cost dictionary
            "cost_after": optimized,
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
        
        # Delegate to the ReplanningAgent
        reoptimized = self.replanner.replan(network)

        return {
            "routes_after": reoptimized["routes"],
            "cost_after": reoptimized, # Return the full cost dictionary
            "fuel_price_after": network["fuel_price"],
            "delay_multiplier": network["delay_factor"],
            "disruption_type": scenario["type"],
            "decision_details": scenario["desc"]
        }

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appagentsplannerpy"></a>
### 📄 app/agents/planner.py

```python
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

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appagentsreplannerpy"></a>
### 📄 app/agents/replanner.py

```python
from app.optimization.vrp_solver import solve_vrp
from app.ml.predict import DelayPredictor

class ReplanningAgent:
    def __init__(self, predictor: DelayPredictor):
        self.predictor = predictor

    def replan(self, network):
        # The core replanning logic is the same as optimizing, but on a disrupted network
        predicted_delays = self.predictor.predict_delays(network)
        solver_result = solve_vrp(
            locations=network["locations"],
            orders=network["orders"],
            fleet=network["fleet"],
            fuel_price=network["fuel_price"],
            driver_cost_per_minute=network.get("driver_cost_per_minute", 0.42),
            predicted_delays=predicted_delays,
            distance_matrix=network.get("distance_matrix"), # Use pre-computed matrix
            depot_time_window=network.get("depot_time_window", (0, 1440))
        )
        return solver_result
```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appapiroutespy"></a>
### 📄 app/api/routes.py

```python
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

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appdatainitpy"></a>
### 📄 app/data/__init__.py

```python
# (Empty file)

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appdatageneratedatapy"></a>
### 📄 app/data/generate_data.py

```python
import math
import random


def generate_locations(num_orders=8):
    depot = (50.0, 50.0)
    locations = [depot]
    for _ in range(num_orders):
        locations.append((random.uniform(10, 90), random.uniform(10, 90)))
    return locations


def generate_orders(locations):
    orders = []
    for idx, loc in enumerate(locations[1:], start=1):
        orders.append({
            "order_id": f"O{idx}",
            "location_index": idx,
            "demand": 1,
        })
    return orders


def generate_fleet(num_vehicles=3):
    fleet = []
    for idx in range(num_vehicles):
        fleet.append({
            "vehicle_id": f"V{idx+1}",
            "capacity": 5,
        })
    return fleet


def generate_distance_matrix(locations):
    size = len(locations)
    matrix = [[0] * size for _ in range(size)]
    for i in range(size):
        for j in range(size):
            dx = locations[i][0] - locations[j][0]
            dy = locations[i][1] - locations[j][1]
            matrix[i][j] = math.hypot(dx, dy)
    return matrix


def generate_delivery_network(num_orders=8, num_vehicles=3):
    locations = generate_locations(num_orders)
    orders = generate_orders(locations)
    fleet = generate_fleet(num_vehicles)
    fuel_price = round(random.uniform(1.2, 1.8), 2)
    return {
        "locations": locations,
        "orders": orders,
        "fleet": fleet,
        "fuel_price": fuel_price,
        "delay_factor": 1.0,
    }

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appdatarealdatapy"></a>
### 📄 app/data/real_data.py

```python
"""
Real delivery dataset loader.
Reads directly from a production-scale CSV dataset.
"""
import pandas as pd
import math
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "deliveries.csv")


def load_dataset_from_csv(filepath=DATA_PATH, num_orders=10, num_vehicles=3, vehicle_capacity=150):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Production dataset not found at {filepath}. Please add the dataset here.")

    df = pd.read_csv(filepath).head(num_orders + 1)
    
    locations = list(zip(df['latitude'], df['longitude']))
    
    # Extract depot info from the first row
    depot_row = df.iloc[0]
    depot_time_window = (
        int(depot_row.get('time_window_start', 0)),
        int(depot_row.get('time_window_end', 1440))
    )

    orders = []
    for idx in range(1, len(locations)):
        row = df.iloc[idx]
        orders.append({
            "order_id": str(row.get('order_id', f"ORD-{idx}")),
            "location_index": idx,
            "demand": int(row.get('demand', 1)),
            "address": str(row.get('address', f"Location {idx}")),
            "coordinates": locations[idx],
            "time_window_start": int(row.get('time_window_start', 0)),
            "time_window_end": int(row.get('time_window_end', 1440)), # Default to full day
        })

    fleet = [
        {"vehicle_id": f"V{i}", "capacity": vehicle_capacity, "type": "truck"}
        for i in range(num_vehicles)
    ]
    
    return {
        "locations": locations,
        "orders": orders,
        "fleet": fleet,
        "depot_time_window": depot_time_window,
        "fuel_price": 1.0,
        "delay_factor": 1.0,
        "city": str(df.iloc[0].get('city', 'Unknown')),
        "dataset_source": "Production CSV",
    }


def generate_delivery_network(source="NYC", num_orders=10, num_vehicles=3, vehicle_capacity=150):
    """
    Load a delivery network from production CSV data.
    """
    return load_dataset_from_csv(DATA_PATH, num_orders, num_vehicles, vehicle_capacity)

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appmainpy"></a>
### 📄 app/main.py

```python
from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Agentic AI Logistics Optimization")
app.include_router(router)

@app.get("/")
def read_root():
    return {"status": "Agentic AI Logistics Optimization API is running"}

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appmlinitpy"></a>
### 📄 app/ml/__init__.py

```python
# (Empty file)

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appmlpredictpy"></a>
### 📄 app/ml/predict.py

```python
import os
import pickle
import numpy as np
from app.ml.train import load_delay_model

MODEL_PATH = os.path.join(os.path.dirname(__file__), "delay_model.pkl")

class DelayPredictor:
    def __init__(self):
        self.model = load_delay_model()

    def predict_delays(self, network):
        # The distance matrix from the network is in centimiles.
        distance_matrix_centi = network.get("distance_matrix")
        if distance_matrix_centi is None:
            from app.optimization.vrp_solver import build_distance_matrix
            distance_matrix_centi = build_distance_matrix(network["locations"])
        
        num_locations = len(network["locations"])
        # Create a matrix for predicted delays between any two nodes
        delay_matrix = [[0.0] * num_locations for _ in range(num_locations)]
        traffic_level = network.get("delay_factor", 1.0)

        for i in range(num_locations):
            for j in range(num_locations):
                if i == j:
                    continue
                distance = distance_matrix_centi[i][j] / 100.0
                features = np.array([[distance, traffic_level]])
                delay = self.model.predict(features)[0]
                delay_matrix[i][j] = max(0.0, float(delay))

        network["predicted_delays"] = delay_matrix # Now it's a matrix
        return delay_matrix

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appmltrainpy"></a>
### 📄 app/ml/train.py

```python
import os
import pickle
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split # Ensure this is imported
from xgboost.callback import EarlyStopping # Re-add this import
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

MODEL_PATH = os.path.join(os.path.dirname(__file__), "delay_model.pkl")
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "historical_delays.csv")


def train_delay_model():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Production dataset missing at {DATA_PATH}. Please provide a large-scale training dataset.")
    
    df = pd.read_csv(DATA_PATH)
    X = df[['distance', 'traffic_level']].values
    y = df['delay'].values
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Optimized XGBoost Regressor...")
    model = xgb.XGBRegressor(objective='reg:squarederror',
                             n_estimators=1000,
                             learning_rate=0.05,
                             max_depth=5,
                             subsample=0.8,
                             colsample_bytree=0.8,
                             random_state=42,
                             n_jobs=-1)
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], callbacks=[EarlyStopping(rounds=50, save_best=True)], verbose=False)
    
    predictions = model.predict(X_test)
    print("\n--- Model Evaluation Metrics ---")
    print(f"MSE: {mean_squared_error(y_test, predictions):.4f}")
    print(f"MAE: {mean_absolute_error(y_test, predictions):.4f}")
    print(f"R2 Score: {r2_score(y_test, predictions):.4f}\n")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    return model


def load_delay_model():
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    return train_delay_model()

if __name__ == "__main__":
    model = train_delay_model()
    print("Trained delay model and saved to", MODEL_PATH)

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appoptimizationinitpy"></a>
### 📄 app/optimization/__init__.py

```python
# (Empty file)

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appoptimizationvrpsolverpy"></a>
### 📄 app/optimization/vrp_solver.py

```python
import math
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in miles using Haversine formula for geographic coordinates."""
    R = 3959  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2)**2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def build_distance_matrix(locations):
    """Build distance matrix, detecting if locations are geographic (lat/lon) or Cartesian."""
    size = len(locations)
    matrix = [[0.0] * size for _ in range(size)]
    
    # Check if locations are geographic coordinates (lat/lon range: -90 to 90, -180 to 180)
    is_geographic = (all(-90 <= loc[0] <= 90 and -180 <= loc[1] <= 180 for loc in locations))
    
    for i in range(size):
        for j in range(size):
            if is_geographic:
                lat1, lon1 = locations[i]
                lat2, lon2 = locations[j]
                distance = haversine_distance(lat1, lon1, lat2, lon2)
                matrix[i][j] = int(distance * 100)  # Convert to centimiles for precision
    
    return matrix


def solve_vrp(locations, orders, fleet, fuel_price, driver_cost_per_minute=0.42, predicted_delays=None, distance_matrix=None, time_limit_seconds=2, depot_time_window=(0, 1440)):
    if distance_matrix is None:
        distance_matrix = build_distance_matrix(locations)
    num_locations = len(locations)
    num_vehicles = len(fleet)
    depot = 0

    demands = [0] * num_locations
    for order in orders:
        demands[order["location_index"]] = order.get("demand", 1)

    vehicle_capacities = [vehicle.get("capacity", 10) for vehicle in fleet]

    manager = pywrapcp.RoutingIndexManager(num_locations, num_vehicles, depot)
    routing = pywrapcp.RoutingModel(manager)

    # --- Add Time Dimension for Time Windows ---
    
    # Service time at each location (in minutes)
    service_times = [0] * num_locations # 0 for depot
    for order in orders:
        service_times[order["location_index"]] = 15 # 15 minutes for all deliveries

    def time_callback(from_index, to_index):
        """Returns the total time between the two nodes."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        
        # Use the ML-predicted delay for travel time if available
        if predicted_delays:
            travel_time = int(predicted_delays[from_node][to_node])
        else:
            # Fallback to simple distance-based calculation (assume 20 mph)
            distance_miles = distance_matrix[from_node][to_node] / 100.0
            travel_time = int(distance_miles * 3)
        
        # Add service time for the from_node
        service_time = service_times[from_node]
        return travel_time + service_time

    time_callback_index = routing.RegisterTransitCallback(time_callback)
    
    routing.AddDimension(
        time_callback_index,
        30,      # slack_max: 30 minutes waiting time allowed at each location
        3000,    # vehicle_capacity: max total time per vehicle (50 hours)
        False,   # fix_start_cumul_to_zero: Don't force start time to be 0
        "Time"
    )
    time_dimension = routing.GetDimensionOrDie("Time")

    # --- Define Financially-Grounded Cost Function ---
    def cost_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        
        # Fuel Cost (distance-based)
        distance_miles = distance_matrix[from_node][to_node] / 100.0
        fuel_cost = distance_miles * fuel_price
        
        # Labor Cost (time-based)
        travel_time_minutes = time_callback(from_index, to_index)
        labor_cost = travel_time_minutes * driver_cost_per_minute
        
        return int((fuel_cost + labor_cost) * 100) # Return cost in cents

    cost_callback_index = routing.RegisterTransitCallback(cost_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(cost_callback_index)

    # Add time window constraints for each order location.
    for order in orders:
        index = manager.NodeToIndex(order["location_index"])
        time_dimension.CumulVar(index).SetRange(order["time_window_start"], order["time_window_end"])

    # Add time window constraint for the depot
    depot_index = manager.NodeToIndex(depot)
    time_dimension.CumulVar(depot_index).SetRange(depot_time_window[0], depot_time_window[1])

    demand_callback_index = routing.RegisterUnaryTransitCallback(lambda index: demands[manager.IndexToNode(index)])
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        vehicle_capacities,
        True,
        "Capacity",
    )

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.seconds = time_limit_seconds
    search_parameters.log_search = False

    solution = routing.SolveWithParameters(search_parameters)
    routes = []
    total_cost_cents = 0
    total_fuel_cost_cents = 0
    total_labor_cost_cents = 0

    if solution:
        total_cost_cents = solution.ObjectiveValue()
        for vehicle_id in range(num_vehicles):
            index = routing.Start(vehicle_id)
            route = []
            route_time = 0
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                route.append(node)
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                if not routing.IsEnd(index):
                    # Calculate fuel and labor cost for this segment
                    from_node = node
                    to_node = manager.IndexToNode(index)
                    distance_miles = distance_matrix[from_node][to_node] / 100.0
                    total_fuel_cost_cents += (distance_miles * fuel_price) * 100
                    
                    segment_time = time_callback(previous_index, index)
                    total_labor_cost_cents += (segment_time * driver_cost_per_minute) * 100
            
            if len(route) > 1:
                routes.append(route)
        
    return {
        "routes": routes,
        "total_cost": total_cost_cents / 100.0 if solution else 0,
        "fuel_cost": total_fuel_cost_cents / 100.0 if solution else 0,
        "labor_cost": total_labor_cost_cents / 100.0 if solution else 0,
        "distance_matrix": distance_matrix,
    }

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="appsessionpy"></a>
### 📄 app/session.py

```python
import pickle
import uuid
import os
import time

SESSION_TTL_SECONDS = 3600  # 1 hour

SESSION_DIR = "temp_sessions"

if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

def _get_session_path(session_id):
    return os.path.join(SESSION_DIR, f"{session_id}.pkl")

def create_session():
    """Creates a new session and returns its ID."""
    return str(uuid.uuid4())

def save_state(session_id, state):
    """Saves state to a session file."""
    with open(_get_session_path(session_id), "wb") as f:
        pickle.dump(state, f)

def load_state(session_id):
    """Loads state from a session file, returning None if not found or expired."""
    filepath = _get_session_path(session_id)
    if not os.path.exists(filepath) or time.time() - os.path.getmtime(filepath) > SESSION_TTL_SECONDS:
        if os.path.exists(filepath): os.remove(filepath)
        return None
    with open(filepath, "rb") as f:
        return pickle.load(f)
```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="apputilsinitpy"></a>
### 📄 app/utils/__init__.py

```python
# (Empty file)

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="apputilscostpy"></a>
### 📄 app/utils/cost.py

```python
def compute_cost(distance, fuel_price, delay, delay_penalty=1.5):
    return distance * fuel_price + delay * delay_penalty

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="apputilsfeaturespy"></a>
### 📄 app/utils/features.py

```python
def build_delay_features(distance, base_speed=40, traffic_factor=1.0):
    return {
        "distance": distance,
        "traffic_factor": traffic_factor,
        "base_travel_time": distance / base_speed,
    }

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="datadeliveriescsv"></a>
### 📄 data/deliveries.csv

```csv
order_id,latitude,longitude,demand,address,city
DEPOT,40.86534118652344,-73.92707061767578,0,NYC Taxi Depot,NYC
ORD-1,40.74940490722656,-73.99177551269531,1,NYC Delivery 1,NYC
ORD-2,40.721805572509766,-73.97529602050781,3,NYC Delivery 2,NYC
ORD-3,40.73733901977539,-73.97962951660156,3,NYC Delivery 3,NYC
ORD-4,40.75555419921875,-73.97563171386719,2,NYC Delivery 4,NYC
ORD-5,40.764591217041016,-73.96166229248047,3,NYC Delivery 5,NYC
ORD-6,40.75785827636719,-73.96041107177734,1,NYC Delivery 6,NYC
ORD-7,40.768123626708984,-73.98106384277344,3,NYC Delivery 7,NYC
ORD-8,40.757720947265625,-73.97148132324219,3,NYC Delivery 8,NYC
ORD-9,40.80255126953125,-73.96768951416016,3,NYC Delivery 9,NYC
ORD-10,40.74822998046875,-73.9925308227539,1,NYC Delivery 10,NYC

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="datahistoricaldelayscsv"></a>
### 📄 data/historical_delays.csv

```csv
distance,traffic_level,delay
0.9311950661783269,1.8,7.583333333333333
1.1219593284041638,1.0,11.05
3.9677609390526816,1.2,35.4
0.9231028497488848,1.8,7.15
0.7386001743058941,1.2,7.25
0.6828932971886214,1.0,7.383333333333334
0.8241621231481521,1.0,5.683333333333334
3.5513433240146344,1.8,25.85
0.8142659938688238,1.0,4.25
3.182338506437816,1.0,20.416666666666668
2.365171223404991,1.0,21.233333333333334
2.3446377052925222,1.2,18.8
1.1555004358956185,1.8,18.566666666666666
0.6162423988863778,1.0,4.333333333333333
3.9663548515295606,1.0,23.566666666666666
0.4080038307145789,1.2,3.5166666666666666
2.130245224208559,1.8,38.6
1.577554815190402,1.8,12.183333333333334
2.861715752345439,1.8,21.95
0.8098651309119229,1.2,4.183333333333334
1.5572063726687688,1.0,8.1
1.071651839273396,1.2,10.866666666666667
1.2845061975851666,1.0,7.05
3.029242340845412,1.8,19.383333333333333
12.802636083355821,1.8,41.416666666666664
2.83333216443162,1.2,21.383333333333333
3.7633240426280308,1.0,18.833333333333332
2.3232899050783278,1.0,11.566666666666666
1.5689653108651833,1.0,14.866666666666667
6.176464349778412,1.2,38.85
2.836481655916958,1.8,24.65
3.369936098838892,1.2,17.466666666666665
2.7958980630221144,1.8,17.033333333333335
6.362229673158341,1.2,37.81666666666667
0.890541718705169,1.2,11.783333333333333
0.9272900164527602,1.8,8.766666666666667
0.7061648005601928,1.2,9.216666666666667
0.5962022829373305,1.0,4.616666666666666
2.0583633179269962,1.2,19.816666666666666
1.6079116370111954,1.8,25.383333333333333
3.4034888154464813,1.0,24.166666666666668
1.389656540061987,1.2,18.366666666666667
1.225547334422149,1.2,22.433333333333334
0.712905851808313,1.0,6.05
1.3663430506485692,1.8,9.316666666666666
5.077663244561718,1.2,24.633333333333333
0.8168097944400039,1.8,5.8
1.1003357421209663,1.8,6.25
3.1493235771084516,1.0,20.283333333333335
2.1606635633421933,1.8,14.6
10.775748891587739,1.0,25.95
2.950429236350447,1.2,27.45
1.2583996105612059,1.8,10.566666666666666
0.7164334342891854,1.2,6.083333333333333
5.976615226077285,1.8,13.65
2.3898534920391254,1.2,58.8
0.9698508874150679,1.2,20.466666666666665
2.8327136447679697,1.2,43.45
1.5641171667381806,1.2,11.583333333333334
2.4986873731991412,1.8,7.866666666666666
1.9444817352888302,1.0,8.766666666666667
1.270267411180335,1.8,12.016666666666667
1.0518241737854204,1.2,8.533333333333333
2.064598802346947,1.2,12.0
0.7576349092484552,1.8,2.9
0.6838015201239857,1.8,7.966666666666667
1.5377409092803804,1.2,13.133333333333333
8.147384822496951,1.0,16.716666666666665
0.38814005944447677,1.0,3.5833333333333335
1.6171296608216141,1.8,14.5
3.62404022150973,1.0,13.566666666666666
0.839745992349871,1.0,10.616666666666667
0.6674460483597608,1.8,9.816666666666666
6.963179202615406,1.8,37.916666666666664
1.7537355957809297,1.0,10.783333333333333
3.3392152416912833,1.2,27.133333333333333
3.053538565484889,1.8,38.95
2.624439280057923,1.0,11.233333333333333
4.030077346441577,1.0,19.833333333333332
3.1601462641844957,1.2,19.85
0.8463214173590524,1.2,13.083333333333334
0.7825438571886331,1.8,8.666666666666666
0.5695423502413604,1.8,3.6333333333333333
0.4911199088943362,1.8,3.7
2.951548850383993,1.0,20.066666666666666
11.666022950689571,1.0,29.7
0.9323060991797876,1.0,19.566666666666666
0.5629276839195392,1.2,5.6
0.9890542424937782,1.2,7.833333333333333
0.860701155956034,1.8,5.766666666666667
0.9199844680712126,1.2,6.983333333333333
6.204371516990284,1.8,29.366666666666667
6.390356450351259,1.2,39.016666666666666
0.8944205331945935,1.2,6.766666666666667
1.3782062838942903,1.8,9.933333333333334
0.8813983255175624,1.0,7.25
1.8557079770066065,1.2,18.466666666666665
9.947264323068307,1.8,47.06666666666667
0.811545348583611,1.8,12.816666666666666
1.7291863434139785,1.2,30.433333333333334
0.5723558422285046,1.0,9.883333333333333
12.341224510590829,1.0,34.416666666666664
1.8741154423113349,1.0,10.883333333333333
12.173463255988935,1.0,31.4
1.4639851626216944,1.8,16.483333333333334
1.5256269638251805,1.2,6.983333333333333
0.7406337790353476,1.2,16.033333333333335
0.6112694569719312,1.8,4.05
0.7603543618772279,1.8,6.216666666666667
0.6499986679930183,1.8,6.4
8.750589220199407,1.8,45.88333333333333
2.4859797392481595,1.0,26.016666666666666
3.1370128802494395,1.0,8.416666666666666
2.0614467521326163,1.2,15.0
16.879128944497342,1.0,35.266666666666666
1.583631961328713,1.0,10.183333333333334
0.658513551365818,1.2,16.2
1.0392093410482888,1.2,10.066666666666666
1.0140129217914151,1.2,9.9
1.3739835385919135,1.0,9.566666666666666
0.6099836335534994,1.2,4.95
0.5230691380449883,1.0,1.6833333333333333
3.911631203146775,1.0,17.35
0.38179098611732903,1.0,3.533333333333333
1.4932956264272772,1.8,7.033333333333333
2.6455167422594092,1.0,22.6
0.23306442340479044,1.0,6.933333333333334
1.1093180374173954,1.2,18.633333333333333
1.8110296304423397,1.8,14.566666666666666
1.2964808129297454,1.0,5.35
0.8852823152988389,1.0,6.666666666666667
0.6598680504973222,1.8,15.566666666666666
0.7900870950663929,1.8,12.883333333333333
0.8308135678529472,1.8,5.616666666666666
1.0354124175128296,1.8,3.9
1.38895162904878,1.2,7.9
5.037619472068664,1.2,21.9
1.8191025660895368,1.0,8.033333333333333
1.7941292651468377,1.0,9.433333333333334
0.5249053933477685,1.0,3.15
2.805552518132014,1.0,15.216666666666667
0.45325521553616127,1.2,12.266666666666667
1.7463863437641993,1.8,11.9
2.1457785910140816,1.0,13.583333333333334
1.3743644039064473,1.0,16.2
0.7059684975535484,1.2,5.3
1.179408502021815,1.8,10.416666666666666
1.4320955896737135,1.0,14.316666666666666
0.9810424259916324,1.0,2.35
2.8261136392076924,1.8,16.383333333333333
0.8101936010198366,1.2,9.416666666666666
0.7279821089705513,1.2,5.85
1.5090042279427653,1.2,5.7
3.1514508945773363,1.0,15.15
0.9272147985036899,1.0,3.783333333333333
1.300667745207652,1.8,17.966666666666665
0.8077066499591206,1.8,15.0
1.0351187798246975,1.8,10.516666666666667
5.415452243123506,1.8,23.083333333333332
0.5827450696036146,1.8,14.483333333333333
1.1313812585094343,1.8,9.566666666666666
0.3111194262264243,1.8,1.7333333333333334
0.829956573235332,1.8,6.966666666666667
1.0680048625573433,1.8,6.383333333333334
4.351211339534609,1.8,18.616666666666667
1.3347807690670448,1.8,24.116666666666667
8.28451993379446,1.8,42.38333333333333
5.786563163858206,1.0,16.35
1.80514088787052,1.0,12.583333333333334
5.376482898952409,1.8,20.95
4.133996642669879,1.2,20.35
1.018473345337743,1.2,15.666666666666666
0.3490541691035334,1.0,2.1
0.5793364641012391,1.8,5.833333333333333
1.1562465800393287,1.8,12.283333333333333
1.5125060603053548,1.2,11.5
0.8914118545054727,1.2,11.183333333333334
0.9866513743494172,1.0,7.716666666666667
0.7756893358030296,1.2,6.116666666666666
1.1441001547319538,1.0,6.15
0.7898652038417615,1.8,6.7
4.640155711237089,1.8,18.216666666666665
1.743663659363187,1.2,10.95
0.8112992292742004,1.2,8.833333333333334
3.542204603418241,1.0,12.216666666666667
1.2289384273967725,1.8,11.65
1.3876381216698503,1.0,4.9
1.1101740567414005,1.2,11.016666666666667
1.087106823014552,1.0,10.866666666666667
2.5360183344925584,1.8,9.766666666666667
2.1756896164982464,1.0,17.616666666666667
0.8557940983998069,1.2,9.666666666666666
1.227490368981834,1.0,19.183333333333334
3.620534644688935,1.8,11.0
1.2893737017865887,1.0,13.383333333333333
2.522222037294698,1.8,32.56666666666667
2.1578771996908555,1.0,17.166666666666668
6.613140188150177,1.2,46.95
0.5202914584326253,1.0,1.4166666666666667

... (File truncated for export due to length, showing first 200 lines) ...

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="downloadkaggledatapy"></a>
### 📄 download_kaggle_data.py

```python
import kagglehub
import os
import zipfile
import pandas as pd
import numpy as np

# This script assumes you have authenticated with Kaggle.
# The most reliable way is to place your kaggle.json file in ~/.kaggle/
# See the README or documentation for instructions.

# Download latest version
path = kagglehub.competition_download('nyc-taxi-trip-duration')
print("Path to competition files:", path)

# --- Extract and Process Data into historical_delays.csv ---
train_zip = os.path.join(path, "train.zip")
train_csv = os.path.join(path, "train.csv")

if os.path.exists(train_zip):
    print("Extracting train.zip...")
    with zipfile.ZipFile(train_zip, 'r') as z:
        z.extractall(path)
    train_csv = os.path.join(path, "train.csv")

if not os.path.exists(train_csv):
    raise FileNotFoundError(f"Could not find train.csv in {path}")

print("Loading dataset into Pandas (sampling 200,000 rows for efficiency)...")
df = pd.read_csv(train_csv, nrows=200000)

# 1. Calculate distance using a vectorized Haversine formula
def haversine_vectorized(lat1, lon1, lat2, lon2):
    R = 3959.0 # Earth radius in miles
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    return R * 2 * np.arcsin(np.sqrt(a))

print("Calculating trip distances...")
df['distance'] = haversine_vectorized(
    df['pickup_latitude'], df['pickup_longitude'],
    df['dropoff_latitude'], df['dropoff_longitude']
)

# 2. Derive traffic level proxy from pickup time
print("Deriving traffic_level proxy from timestamps...")
df['pickup_datetime'] = pd.to_datetime(df['pickup_datetime'])
df['hour'] = df['pickup_datetime'].dt.hour

# Rule: Rush hours = 1.8, Mid-day = 1.2, Off-peak = 1.0
conditions = [
    (df['hour'].between(7, 10)) | (df['hour'].between(16, 19)),
    (df['hour'].between(11, 15))
]
df['traffic_level'] = np.select(conditions, [1.8, 1.2], default=1.0)

# 3. Compute delay (convert trip_duration from seconds to minutes)
df['delay'] = df['trip_duration'] / 60.0

# 4. Filter anomalies for clean ML training
print("Cleaning anomalous data...")
df = df[(df['distance'] > 0.1) & (df['distance'] < 50)]
df = df[(df['delay'] > 1) & (df['delay'] < 120)]

# 5. Format and save the final ML dataframe
final_df = df[['distance', 'traffic_level', 'delay']]

output_dir = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(output_dir, exist_ok=True)
out_file = os.path.join(output_dir, "historical_delays.csv")

final_df.to_csv(out_file, index=False)
print(f"Success! {len(final_df)} rows processed and saved to {out_file}")

# 6. Generate deliveries.csv from the same dataset for the VRP Solver
print("Generating deliveries.csv for routing optimization...")
sample_df = df.sample(200, random_state=42)

delivery_records = []
for i, (_, row) in enumerate(sample_df.iterrows()):
    if i == 0:
        delivery_records.append({
            "order_id": "DEPOT",
            "latitude": row['pickup_latitude'],
            "longitude": row['pickup_longitude'],
            "demand": 0,
            "address": "NYC Taxi Depot",
            "city": "NYC",
            "time_window_start": 8 * 60,  # 8 AM in minutes
            "time_window_end": 18 * 60,   # 6 PM in minutes
        })
    else:
        # Assign morning or afternoon delivery windows
        if i % 2 == 0:
            time_start, time_end = (9 * 60, 12 * 60)  # 9 AM - 12 PM
        else:
            time_start, time_end = (13 * 60, 16 * 60) # 1 PM - 4 PM

        delivery_records.append({
            "order_id": f"ORD-{i}",
            "latitude": row['dropoff_latitude'],
            "longitude": row['dropoff_longitude'],
            "demand": np.random.randint(1, 4),
            "address": f"NYC Delivery {i}",
            "city": "NYC",
            "time_window_start": time_start,
            "time_window_end": time_end,
        })

delivery_out_file = os.path.join(output_dir, "deliveries.csv")
pd.DataFrame(delivery_records).to_csv(delivery_out_file, index=False)
print(f"Success! Created production routing dataset at {delivery_out_file}")

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="frontendapppy"></a>
### 📄 frontend/app.py

```python
import streamlit as st
import requests
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import altair as alt
from pathlib import Path
import os

BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(layout="wide", page_title="Logistics VRP")

st.title("Agentic AI — Logistics Optimization")

# Data loading: prefer Kaggle/local file, otherwise ask backend to generate
data_file = Path("data/deliveries.csv")
if data_file.exists():
    df = pd.read_csv(data_file)
    st.success(f"Loaded local data: {data_file} ({len(df)} rows)")
else:
    st.warning("No local data/deliveries.csv found. Ensure the dataset is present or optimization may fail.")
    df = None

# Initialize session state for holding the API session_id
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'results' not in st.session_state:
    st.session_state.results = None

col1, col2 = st.columns([1, 2])
with col1:
    st.header("Controls")
    num_vehicles = st.number_input("Num vehicles", value=4, min_value=1, max_value=20)
    vehicle_capacity = st.number_input("Vehicle capacity", value=150, min_value=10, max_value=500)
    num_orders = st.number_input("Num orders (destinations)", value=25, min_value=5, max_value=150)
    fuel_price = st.number_input("Fuel price (per unit distance)", value=1.0, step=0.1)
    driver_hourly_wage = st.number_input("Driver Hourly Wage ($)", value=25.0, step=1.0)
    scenario_options = ["Random", "Accident on Route", "Severe Weather", "Road Block / Protest", "Fuel Price Spike"]
    selected_scenario = st.selectbox("Disruption Scenario", scenario_options)
    run_opt = st.button("Run initial optimization")
    run_sim = st.button("Simulate selected disruption")

def format_time(minutes):
    """Converts minutes from midnight to HH:MM format."""
    if minutes is None:
        return "Any"
    h = int(minutes // 60)
    m = int(minutes % 60)
    return f"{h:02d}:{m:02d}"

def plot_routes_on_map(routes_before, routes_after=None, center=None, locations=None, orders=None, depot_time_window=None):
    if center is None:
        # compute center
        all_coords = []
        for r in (routes_before or []) + (routes_after or []):
            for p in r.get("coords", []):
                all_coords.append(p)
        if not all_coords:
                center = [0.0, 0.0]
        else:
                lat = float(np.mean([c[0] for c in all_coords]))
                lon = float(np.mean([c[1] for c in all_coords]))
                center = [lat, lon]

    m = folium.Map(location=center, zoom_start=12)
    
    fg_before = folium.FeatureGroup(name="Before Disruption (Blue)")
    fg_after = folium.FeatureGroup(name="After Disruption (Red Dashed)")
    fg_locations = folium.FeatureGroup(name="Delivery Locations", show=True)

    # Add markers for all locations with time windows
    if locations and orders:
        # Depot Marker
        if depot_time_window:
            depot_start = format_time(depot_time_window[0])
            depot_end = format_time(depot_time_window[1])
            depot_tooltip = f"Depot (Open: {depot_start} - {depot_end})"
        else:
            depot_tooltip = "Depot"
        folium.Marker(
            location=locations[0],
            icon=folium.Icon(color="green", icon="home"),
            tooltip=depot_tooltip
        ).add_to(fg_locations)

        # Order Markers
        for order in orders:
            loc_idx = order["location_index"]
            start_time = format_time(order.get("time_window_start"))
            end_time = format_time(order.get("time_window_end"))
            tooltip = f"Order {order['order_id']}<br>Window: {start_time} - {end_time}"
            folium.Marker(
                location=locations[loc_idx],
                icon=folium.Icon(color="gray", icon="cube", prefix="fa"),
                tooltip=tooltip
            ).add_to(fg_locations)

    # draw before routes (blue)
    for i, r in enumerate(routes_before or []):
        coords = r.get("coords", [])
        if not coords: continue
        clean_coords = [[float(pt[0]), float(pt[1])] for pt in coords]
        folium.PolyLine(locations=clean_coords, color="blue", weight=4, opacity=0.5, tooltip=f"Before - Vehicle {i}").add_to(fg_before)
    # draw after routes (red)
    for i, r in enumerate(routes_after or []):
        coords = r.get("coords", [])
        if not coords: continue
        clean_coords = [[float(pt[0]), float(pt[1])] for pt in coords]
        folium.PolyLine(locations=clean_coords, color="red", weight=5, opacity=0.9, dash_array='10, 10', tooltip=f"After - Vehicle {i}").add_to(fg_after)
        
    fg_before.add_to(m)
    if routes_after:
        fg_after.add_to(m)
    fg_locations.add_to(m)
    folium.LayerControl().add_to(m)
    return m

def show_comparison_charts(metrics_data):
    """Renders separate interactive line charts for each metric."""
    if not metrics_data:
        return

    df = pd.DataFrame(metrics_data)
    
    # Use columns for a better side-by-side layout
    cols = st.columns(len(df['Metric'].unique()))
    
    for i, metric in enumerate(df['Metric'].unique()):
        with cols[i]:
            metric_df = df[df['Metric'] == metric]
            metric_df_melted = metric_df.melt(id_vars=['Metric'], value_vars=['Before', 'After'], var_name='Scenario', value_name='Value')

            chart = alt.Chart(metric_df_melted).mark_bar().encode(
                x=alt.X('Scenario:N', title=None, axis=alt.Axis(labelAngle=0, grid=False)),
                y=alt.Y('Value:Q', title=None, scale=alt.Scale(zero=False)),
                color=alt.Color('Scenario:N', 
                              scale=alt.Scale(domain=['Before', 'After'], range=['#1f77b4', '#d62728']), # Blue for Before, Red for After
                              legend=None), # Legend is redundant with x-axis
                tooltip=[alt.Tooltip('Value:Q', format='.2f')]
            ).properties(
                title=alt.TitleParams(text=metric, anchor='middle')
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in miles using Haversine formula."""
    R = 3959  # Earth radius in miles
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (np.sin(dlat/2)**2 + 
         np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * 
         np.sin(dlon/2)**2)
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def calculate_total_distance(routes, locations):
    """Calculates the total distance for a set of routes."""
    total_distance = 0
    if not routes or not locations:
        return 0
    for route in routes:
        sequence = route.get("route", [])
        for j in range(len(sequence) - 1):
            if sequence[j] < len(locations) and sequence[j+1] < len(locations):
                loc1 = locations[sequence[j]]
                loc2 = locations[sequence[j+1]]
                total_distance += haversine_distance(loc1[0], loc1[1], loc2[0], loc2[1])
    return total_distance

def display_route_details(title, routes, locations):
    st.subheader(title)
    for i, route in enumerate(routes):
        with st.expander(f"Vehicle {i+1} Details"):
            sequence = route.get("route", [])
            st.write(f"**Sequence:** `{' -> '.join(map(str, sequence))}`")
            
            total_distance = 0
            for j in range(len(sequence) - 1):
                loc1 = locations[sequence[j]]
                loc2 = locations[sequence[j+1]]
                total_distance += haversine_distance(loc1[0], loc1[1], loc2[0], loc2[1])
            st.metric("Route Distance", f"{total_distance:.2f} miles")

def calculate_capacity_utilization(routes, orders, vehicle_capacity):
    """Calculates the average capacity utilization across all vehicles."""
    if not routes:
        return 0
    
    total_utilization = 0
    order_demands = {order['location_index']: order['demand'] for order in orders}
    
    for route in routes:
        route_demand = sum(order_demands.get(node, 0) for node in route.get("route", []))
        utilization = (route_demand / vehicle_capacity) * 100 if vehicle_capacity > 0 else 0
        total_utilization += utilization
        
    return total_utilization / len(routes)

def display_results(results_data):
    """Renders the entire results dashboard using tabs."""
    
    # Extract data with defaults
    cost_before = results_data.get("cost_before", 0)
    cost_after = results_data.get("cost_after", cost_before) # Default to cost_before if no disruption
    disruption = results_data.get("disruption")
    decision_details = results_data.get("decision_details")
    routes_before = results_data.get("routes_before") or results_data.get("routes", [])
    routes_after = results_data.get("routes_after") if disruption else None
    locations = results_data.get("locations", [])
    orders = results_data.get("orders", [])
    depot_time_window = results_data.get("depot_time_window")

    # --- Main Dashboard Area ---
    st.header("📊 Optimization Dashboard")

    # Display disruption info if it exists
    if disruption:
        st.warning(f"**Disruption Event:** {disruption}")
        st.info(f"**Agent Decision & Rationale:** {decision_details}")

    # KPI Metrics
    total_distance_before = calculate_total_distance(routes_before, locations)
    total_distance_after = calculate_total_distance(routes_after, locations) if routes_after else total_distance_before
    num_vehicles_after = len(routes_after) if routes_after else len(routes_before)
    utilization_before = calculate_capacity_utilization(routes_before, orders, int(vehicle_capacity))
    utilization_after = calculate_capacity_utilization(routes_after, orders, int(vehicle_capacity)) if routes_after else utilization_before
    
    # Extract total_cost from the cost dictionaries
    total_cost_before_val = cost_before.get("total_cost", 0)
    total_cost_after_val = cost_after.get("total_cost", total_cost_before_val)

    kpi_cols = st.columns(6)
    kpi_cols[0].metric("Initial Cost", f"{total_cost_before_val:.2f}")
    kpi_cols[1].metric("Optimized Cost", f"{total_cost_after_val:.2f}", delta=f"{(total_cost_after_val - total_cost_before_val):.2f}")
    kpi_cols[2].metric("Total Distance", f"{total_distance_after:.1f} mi", delta=f"{(total_distance_after - total_distance_before):.1f} mi")
    kpi_cols[3].metric("Vehicles Used", num_vehicles_after, delta=num_vehicles_after - len(routes_before))
    kpi_cols[4].metric("Avg. Capacity Use", f"{utilization_after:.1f}%", delta=f"{(utilization_after - utilization_before):.1f}%")
    kpi_cols[5].metric("Total Deliveries", len(orders))

    # --- Tabs for Detailed Views ---
    map_tab, details_tab, chart_tab, data_tab = st.tabs(["🗺️ Route Map", "⚙️ Route Details", "📈 Comparison Chart", "📋 Raw Data"])

    with map_tab:
        st.subheader("Vehicle Route Visualization")
        m = plot_routes_on_map(
            routes_before, 
            routes_after, 
            locations=locations, 
            orders=orders,
            depot_time_window=depot_time_window
        )
        folium_static(m, width=950, height=600)

    with details_tab:
        if routes_after:
            col_before, col_after = st.columns(2)
            with col_before:
                display_route_details("Route Analysis (Before Disruption)", routes_before, locations)
            with col_after:
                display_route_details("Route Analysis (After Disruption)", routes_after, locations)
        else:
            display_route_details("Initial Route Plan", routes_before, locations)

    with chart_tab:
        st.subheader("Metric Comparison")
        # Calculate metrics for charting
        num_orders_val = len(orders) if len(orders) > 0 else 1 # Avoid division by zero

        num_vehicles_before = len(routes_before)
        avg_dist_before = total_distance_before / num_orders_val

        # If there's no 'after' route, use the 'before' values for comparison
        if routes_after:
            avg_dist_after = total_distance_after / num_orders_val
        else:
            avg_dist_after = avg_dist_before

        # Extract cost breakdown if available
        cost_details_before = results_data.get("cost_before", {})
        cost_details_after = results_data.get("cost_after", cost_details_before)

        metrics_to_plot = [
            {'Metric': 'Total Cost ($)', 'Before': cost_details_before.get("total_cost", 0), 'After': cost_details_after.get("total_cost", 0)},
            {'Metric': 'Total Distance (miles)', 'Before': total_distance_before, 'After': total_distance_after},
            {'Metric': 'Fuel Cost ($)', 'Before': cost_details_before.get("fuel_cost", 0), 'After': cost_details_after.get("fuel_cost", 0)},
            {'Metric': 'Labor Cost ($)', 'Before': cost_details_before.get("labor_cost", 0), 'After': cost_details_after.get("labor_cost", 0)},
        ]
        show_comparison_charts(metrics_to_plot)

    with data_tab:
        st.subheader("Raw Route Output")
        if routes_after:
            st.write("Routes Before Disruption:")
            st.json(routes_before)
            st.write("Routes After Disruption:")
            st.json(routes_after)
        else:
            st.write("Initial Routes:")
            st.json(routes_before)


# handle initial optimize
if run_opt:
    payload = {
        "num_vehicles": int(num_vehicles),
        "vehicle_capacity": int(vehicle_capacity),
        "fuel_price": float(fuel_price),
        "driver_hourly_wage": float(driver_hourly_wage),
        "num_orders": int(num_orders),
        "source": "NYC"
    }
    try:
        with st.spinner("Running initial optimization... This may take a moment for large datasets."):
            resp = requests.post(f"{BASE_URL}/optimize", json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            st.session_state.session_id = data.get("session_id")
            st.session_state.results = data
    except Exception as e:
        st.error(f"Optimize API error: {e}")
        st.stop()

# handle simulate / disruption
if run_sim:
    try:
        if not st.session_state.session_id:
            st.error("Please run an initial optimization first to start a session.")
            st.stop()
        with st.spinner(f"Simulating '{selected_scenario}' disruption and replanning..."):
            params = {"session_id": st.session_state.session_id}
            if selected_scenario != "Random":
                params["scenario"] = selected_scenario
            resp = requests.get(f"{BASE_URL}/simulate", params=params, timeout=60)
            resp.raise_for_status()
            sim_data = resp.json()
            st.session_state.results = sim_data
    except Exception as e:
        st.error(f"Simulate API error: {e}")
        st.stop()


# --- Main Display Area ---
if st.session_state.results:
    display_results(st.session_state.results)
else:
    st.info("Click 'Run initial optimization' to begin.")

st.markdown("---")
st.markdown("Notes: This system uses Folium/OpenStreetMap for maps to avoid paid APIs. Ensure a production Kaggle dataset is placed at data/deliveries.csv (see README).")

```

[⬆ Back to Folder Structure](#folder-structure)

---

<a id="requirementstxt"></a>
### 📄 requirements.txt

```text
fastapi
uvicorn[standard]
streamlit
scikit-learn
pandas
numpy
matplotlib
ortools
requests
python-multipart
folium
streamlit-folium
kagglehub
xgboost
altair

```

[⬆ Back to Folder Structure](#folder-structure)

---

