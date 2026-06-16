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
