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
