from constants import PRIORITY_START, PRIORITY_STOP, VEHICLE_PASS_TIME

class TrafficController:
    def __init__(self):
        self.current_green_road = 'A' # Start with Road A
        self.is_priority_mode = False
        self.timer = 5.0 # Initial green time

    def update(self, lanes, dt):
        self.timer -= dt
        
        # Check Priority Condition (Rule 3.3 in PDF)
        al2_count = lanes['AL2'].count()
        
        if al2_count > PRIORITY_START:
            self.is_priority_mode = True
            self.current_green_road = 'A'
        elif self.is_priority_mode and al2_count < PRIORITY_STOP:
            self.is_priority_mode = False
            self.timer = 0 # Force switch immediately

        # Switch Lights if timer expires and NOT in priority mode
        if self.timer <= 0 and not self.is_priority_mode:
            self.switch_road(lanes)

    def switch_road(self, lanes):
        roads = ['A', 'B', 'C', 'D']
        current_idx = roads.index(self.current_green_road)
        self.current_green_road = roads[(current_idx + 1) % 4]
        
        # Calculate Green Time using formula: |V| * t
        # We average the vehicles in the 3 lanes of the new green road
        next_road = self.current_green_road
        total_vehicles = sum(lanes[f"{next_road}L{i}"].count() for i in range(1, 4))
        avg_v = total_vehicles / 3.0
        
        # Minimum time of 3s, otherwise based on count
        self.timer = max(3.0, avg_v * VEHICLE_PASS_TIME)