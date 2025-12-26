import random
import time
from datetime import datetime
from constants import ROAD_A, ROAD_B, ROAD_C, ROAD_D


class TrafficGenerator:
    """
    Simulates vehicle arrivals at 4 roads and writes vehicle data to text files.
    """
    
    def __init__(self):
        self.road_files = {
            ROAD_A: 'lanea.txt',
            ROAD_B: 'laneb.txt',
            ROAD_C: 'lanec.txt',
            ROAD_D: 'laned.txt'
        }
        self.start_time = time.time()
        self.burst_probability = 0.15  # 15% chance of burst on Road A
        self.burst_size_range = (12, 20)  # Number of vehicles in a burst
        
    def clear_files(self):
        """Clear all lane files before starting new simulation."""
        for file_path in self.road_files.values():
            with open(file_path, 'w') as f:
                f.write('')
    
    def get_arrival_time(self):
        """Get current simulation time in seconds."""
        return time.time() - self.start_time
    
    def write_vehicle(self, road_id):
        """Write a vehicle entry to the corresponding lane file."""
        arrival_time = self.get_arrival_time()
        file_path = self.road_files[road_id]
        
        with open(file_path, 'a') as f:
            f.write(f"{arrival_time}\n")
    
    def generate_normal_traffic(self, duration=60):
        """
        Generate normal traffic flow for all roads.
        Uses random intervals between vehicle arrivals.
        
        Args:
            duration: Duration of simulation in seconds
        """
        self.clear_files()
        print("Starting traffic simulation...")
        print(f"Simulation duration: {duration} seconds")
        
        end_time = time.time() + duration
        next_arrival = {
            ROAD_A: time.time() + random.uniform(1, 3),
            ROAD_B: time.time() + random.uniform(1, 3),
            ROAD_C: time.time() + random.uniform(1, 3),
            ROAD_D: time.time() + random.uniform(1, 3)
        }
        
        while time.time() < end_time:
            current_time = time.time()
            
            # Check for burst on Road A
            if random.random() < self.burst_probability and current_time >= next_arrival[ROAD_A]:
                burst_size = random.randint(*self.burst_size_range)
                print(f"BURST: Generating {burst_size} vehicles on Road A at time {self.get_arrival_time():.2f}s")
                for _ in range(burst_size):
                    self.write_vehicle(ROAD_A)
                # Set next normal arrival for Road A after burst
                next_arrival[ROAD_A] = current_time + random.uniform(2, 4)
            
            # Generate normal traffic for each road
            for road_id in [ROAD_A, ROAD_B, ROAD_C, ROAD_D]:
                if current_time >= next_arrival[road_id]:
                    self.write_vehicle(road_id)
                    # Random interval between 1-4 seconds for normal traffic
                    next_arrival[road_id] = current_time + random.uniform(1, 4)
            
            # Small sleep to prevent CPU spinning
            time.sleep(0.1)
        
        print("\nTraffic simulation completed!")
        self.print_statistics()
    
    def print_statistics(self):
        """Print statistics about generated vehicles."""
        print("\n=== Traffic Statistics ===")
        total_vehicles = 0
        for road_id, file_path in self.road_files.items():
            try:
                with open(file_path, 'r') as f:
                    lines = [line.strip() for line in f if line.strip()]
                    count = len(lines)
                    total_vehicles += count
                    print(f"Road {road_id}: {count} vehicles")
            except FileNotFoundError:
                print(f"Road {road_id}: 0 vehicles (file not found)")
        
        print(f"\nTotal vehicles: {total_vehicles}")


if __name__ == "__main__":
    generator = TrafficGenerator()
    
    # Run simulation for 60 seconds
    # Adjust duration as needed
    generator.generate_normal_traffic(duration=60)

