from collections import deque
from enum import Enum


class LaneType(Enum):
    INCOMING = "Incoming"
    OUTGOING = "Outgoing"
    FREE_LEFT = "Free-Left"


class Vehicle:
    
    def __init__(self, arrival_time):
        self.arrival_time = arrival_time
    
    def __repr__(self):
        return f"Vehicle(arrival_time={self.arrival_time})"


class Lane(deque):
    
    def __init__(self, lane_id, lane_type):
        super().__init__()
        self.lane_id = lane_id
        self.lane_type = lane_type
    
    def enqueue(self, vehicle):
        self.append(vehicle)
    
    def dequeue(self):
        if self.is_empty():
            return None
        return self.popleft()
    
    def is_empty(self):
        return len(self) == 0
    
    def peek(self):
        if self.is_empty():
            return None
        return self[0]
    
    def __repr__(self):
        return f"Lane(id='{self.lane_id}', type={self.lane_type.value}, vehicles={len(self)})"

