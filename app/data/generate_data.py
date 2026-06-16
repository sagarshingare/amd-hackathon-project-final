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
