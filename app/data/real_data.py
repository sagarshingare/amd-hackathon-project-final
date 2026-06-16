"""
Real delivery dataset loader.
Reads directly from a production-scale CSV dataset.
"""
import pandas as pd
import math
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "deliveries.csv")

def load_dataset_from_csv(filepath=DATA_PATH, num_orders=10):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Production dataset not found at {filepath}. Please add the dataset here.")

    df = pd.read_csv(filepath).head(num_orders + 1)
    
    locations = list(zip(df['latitude'], df['longitude']))
    
    orders = []
    for idx in range(1, len(locations)):
        row = df.iloc[idx]
        orders.append({
            "order_id": str(row.get('order_id', f"ORD-{idx}")),
            "location_index": idx,
            "demand": int(row.get('demand', 1)),
            "address": str(row.get('address', f"Location {idx}")),
            "coordinates": locations[idx],
        })

    fleet = [
        {"vehicle_id": "Van1", "capacity": 50, "type": "van"},
        {"vehicle_id": "Van2", "capacity": 50, "type": "van"},
        {"vehicle_id": "Truck1", "capacity": 100, "type": "truck"},
    ]
    
    return {
        "locations": locations,
        "orders": orders,
        "fleet": fleet,
        "fuel_price": 1.5,
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


def generate_delivery_network(source="NYC", num_orders=10):
    """
    Load a delivery network from production CSV data.
    """
    return load_dataset_from_csv(DATA_PATH, num_orders)
