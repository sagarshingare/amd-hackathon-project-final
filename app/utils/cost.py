def compute_cost(distance, fuel_price, delay, delay_penalty=1.5):
    return distance * fuel_price + delay * delay_penalty
