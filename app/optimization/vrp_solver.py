import math
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def euclidean_distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


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
            else:
                distance = euclidean_distance(locations[i], locations[j])
                matrix[i][j] = int(distance * 10)
    
    return matrix


def solve_vrp(locations, orders, fleet, fuel_price, predicted_delays=None):
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

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        distance = distance_matrix[from_node][to_node]
        delay_cost = 0
        if predicted_delays is not None:
            delay_cost = int(predicted_delays[to_node] * 100)
        return int(distance * fuel_price + delay_cost)
        return int(distance * fuel_price + delay_cost)

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

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
    search_parameters.time_limit.seconds = 2
    search_parameters.log_search = False

    solution = routing.SolveWithParameters(search_parameters)
    routes = []
    total_cost = 0

    if solution:
        for vehicle_id in range(num_vehicles):
            index = routing.Start(vehicle_id)
            route = []
            route_distance = 0
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                route.append(node)
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                if not routing.IsEnd(index):
                    next_node = manager.IndexToNode(index)
                    route_distance += distance_matrix[node][next_node]
            if len(route) > 1:
                routes.append(route)
        total_cost = solution.ObjectiveValue()

    return {
        "routes": routes,
        "total_cost": total_cost,
        "distance_matrix": distance_matrix,
    }
