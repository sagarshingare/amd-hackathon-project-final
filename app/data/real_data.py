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


def generate_distance_matrix(locations):
    """
    Calculate distance matrix using Haversine formula for real lat/lon coordinates.
    """
    size = len(locations)
    matrix = [[0.0] * size for _ in range(size)]
    
    for i in range(size):
        for j in range(size):
            lat1, lon1 = locations[i]
            lat2, lon2 = locations[j]
            
            # Haversine formula
            R = 3959  # Earth radius in miles
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = (math.sin(dlat/2)**2 + 
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                 math.sin(dlon/2)**2)
            c = 2 * math.asin(math.sqrt(a))
            matrix[i][j] = R * c
    
    return matrix


def generate_delivery_network(source="NYC", num_orders=10, num_vehicles=3, vehicle_capacity=150):
    """
    Load a delivery network from production CSV data.
    """
    return load_dataset_from_csv(DATA_PATH, num_orders, num_vehicles, vehicle_capacity)
