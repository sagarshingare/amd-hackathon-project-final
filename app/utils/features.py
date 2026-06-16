def build_delay_features(distance, base_speed=40, traffic_factor=1.0):
    return {
        "distance": distance,
        "traffic_factor": traffic_factor,
        "base_travel_time": distance / base_speed,
    }
