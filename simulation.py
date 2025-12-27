import random
from collections import deque
import math
import heapq
from utils import *

class TrafficLight:
    def __init__(self):
        self.state = 'RED'

class Vehicle:
    def __init__(self, v_id, lane):
        self.id = v_id
        self.lane = lane
        self.x = 0
        self.y = 0
        self.angle = 0
        self.path = []
        self.path_index = 0
        self.state = 'QUEUED' # QUEUED, STOPPED, MOVING
        
        # Init physics
        self.speed = 0

    def set_path(self, path):
        self.path = path
        self.state = 'MOVING'
        if path:
            self.x, self.y = path[0]

    def update(self):
        if self.state == 'MOVING' and self.path:
            # Simple point to point
            target = self.path[self.path_index]
            dx = target[0] - self.x
            dy = target[1] - self.y
            dist = math.hypot(dx, dy)
            
            if dist < 5:
                self.path_index += 1
                if self.path_index >= len(self.path):
                    self.state = 'EXITED'
                    return
            
            # Move
            self.angle = math.atan2(dy, dx)
            self.x += math.cos(self.angle) * MAX_SPEED
            self.y += math.sin(self.angle) * MAX_SPEED

class Lane:
    def __init__(self, name, road_id):
        self.name = name # L1, L2, L3
        self.road_id = road_id
        self.vehicles = deque()
        self.light = TrafficLight()
        self.stop_pos = (0,0) # To be set by Intersection

class Road:
    def __init__(self, r_id):
        self.id = r_id
        self.L1 = Lane('L1', r_id) # Incoming
        self.L2 = Lane('L2', r_id) # Priority
        self.L3 = Lane('L3', r_id) # Free Left
        self.lanes = [self.L1, self.L2, self.L3]
        
    def get_waiting_count(self):
        # Count vehicles waiting in L1 and L2 (L3 is free flow usually)
        # But for Green Light calculation, assume L1 + L2
        return len(self.L1.vehicles) + len(self.L2.vehicles)

class Intersection:
    def __init__(self):
        self.roads = {
            'A': Road('A'), 'B': Road('B'), 'C': Road('C'), 'D': Road('D')
        }
        self.timer = 0
        self.green_duration = 180 # Default
        self.current_green_idx = 0 # 0=A,1=B,2=C,3=D
        self.order = ['A', 'B', 'C', 'D']
        self.priority_mode = False
        self.p_road = None
        self.moving_vehicles = []
        
        self._setup_coordinates()

    def add_vehicle(self, r_id, l_id):
        if r_id in self.roads:
            lane = getattr(self.roads[r_id], l_id)
            v_id = f"{r_id}{l_id}_{random.randint(1000,9999)}"
            lane.vehicles.append(Vehicle(v_id, lane))

    def _setup_coordinates(self):
        half = INTERSECTION_SIZE // 2
        
        # A (Top)
        self.roads['A'].L1.stop_pos = (CX - 0.5*LANE_WIDTH, CY - half)
        self.roads['A'].L2.stop_pos = (CX - 1.5*LANE_WIDTH, CY - half)
        self.roads['A'].L3.stop_pos = (CX - 2.5*LANE_WIDTH, CY - half)
        
        # B (Right)
        self.roads['B'].L1.stop_pos = (CX + half, CY - 0.5*LANE_WIDTH)
        self.roads['B'].L2.stop_pos = (CX + half, CY - 1.5*LANE_WIDTH)
        self.roads['B'].L3.stop_pos = (CX + half, CY - 2.5*LANE_WIDTH)
        
        # C (Bottom)
        self.roads['C'].L1.stop_pos = (CX + 0.5*LANE_WIDTH, CY + half)
        self.roads['C'].L2.stop_pos = (CX + 1.5*LANE_WIDTH, CY + half)
        self.roads['C'].L3.stop_pos = (CX + 2.5*LANE_WIDTH, CY + half)
        
        # D (Left)
        self.roads['D'].L1.stop_pos = (CX - half, CY + 0.5*LANE_WIDTH)
        self.roads['D'].L2.stop_pos = (CX - half, CY + 1.5*LANE_WIDTH)
        self.roads['D'].L3.stop_pos = (CX - half, CY + 2.5*LANE_WIDTH)

    def update(self):
        # 1. Check Priority Condition (AL2 > 10)
        # Note: Assignment says "If AL2 accumulates > 10... assigned highest priority... served first until count drops below 5."
        # Does this apply to other roads? "Lane 2 (AL2, BL2, etc.) ... Note: AL2 is the priority lane."
        # This implies AL2 is SPECIAL.
        
        al2_count = len(self.roads['A'].L2.vehicles)
        
        if not self.priority_mode:
            if al2_count > 10:
                self.priority_mode = True
                self.p_road = 'A'
                print(">>> ENTERING PRIORITY MODE (AL2 High Traffic) <<<")
        else:
            # Hysteresis: Stay in priority mode until AL2 < 5
            if al2_count < 5:
                self.priority_mode = False
                self.p_road = None
                self.timer = 0 # Reset timer for normal cycle
                print("<<< EXITING PRIORITY MODE >>>")

        # 2. Update Lights based on Mode
        if self.priority_mode:
            self._set_lights(self.p_road)
        else:
            # Normal Round Robin logic
            self.timer += 1
            if self.timer > self.green_duration:
                self.timer = 0
                self.current_green_idx = (self.current_green_idx + 1) % 4
                
                # Calculate Dynamic Green Time for NEXT road
                next_road_id = self.order[self.current_green_idx]
                r_obj = self.roads[next_road_id]
                
                # Formula: |V| * t
                # |V| = 1/n * sum(|Li|) -> Average vehicles per lane?
                # Let's sum L1+L2 (L3 is free) and average by 2?
                # Or sum L1+L2.
                waiting = r_obj.get_waiting_count()
                avg_waiting = waiting / 2.0 if waiting > 0 else 0
                
                t = 20 # Frames per vehicle estimate (approx 0.3s)
                # Assignment: "t is estimated time for one vehicle to pass"
                
                # Base time + Dynamic
                self.green_duration = max(120, int(waiting * t)) # Min 2s
                # Cap it?
                self.green_duration = min(self.green_duration, 600) # Max 10s
                
            curr_id = self.order[self.current_green_idx]
            self._set_lights(curr_id)

        # 3. Release Vehicles (Simulation Step)
        self._release_vehicles()

    def _set_lights(self, green_road_id):
        for r_id, road in self.roads.items():
            state = 'GREEN' if r_id == green_road_id else 'RED'
            road.L1.light.state = state
            road.L2.light.state = state
            road.L3.light.state = 'GREEN' # Always Free Left

    def _release_vehicles(self):
        # Simple probabilistic release to prevent overlap if we spam
        # Or structured release? 
        # Assignment: "The traffic generator must send vehicle data... simulator polls socket... update lane queues"
        # Serving: "Calculate vehicles served at once"
        
        # We need to pop vehicles from GREEN lanes
        for r in self.roads.values():
            for l in [r.L1, r.L2, r.L3]:
                if l.light.state == 'GREEN' and l.vehicles:
                    # Release rate control (don't dump all at once in one frame)
                    if random.random() < 0.05: # e.g. 1 car every 20 frames avg ~ 3 cars/sec
                        v = l.vehicles.popleft()
                        self._route_vehicle(v, l)

    def _route_vehicle(self, v, lane):
        start = lane.stop_pos
        rid = lane.road_id
        
        # Destination Logic
        # L3 -> Free Left
        # L1, L2 -> Straight (for simplicity, or L1->Left/Straight, L2->Right?)
        # Let's keep it simple: L3->Left, Others->Straight
        
        if lane.name == 'L3':
            # Left Turn relative to approach
            # A(Top) -> B(Right)
            target_map = {'A': 'B', 'B': 'C', 'C': 'D', 'D': 'A'}
            d_id = target_map[rid]
        else:
            # Straight (Opposite)
            target_map = {'A': 'C', 'B': 'D', 'C': 'A', 'D': 'B'}
            d_id = target_map[rid]
            
        ends = {
            'A': (CX + LANE_WIDTH, 0),
            'B': (SCREEN_WIDTH, CY + LANE_WIDTH),
            'C': (CX - LANE_WIDTH, SCREEN_HEIGHT),
            'D': (0, CY - LANE_WIDTH)
        }
        
        dest = ends[d_id]
        path = Utils.get_turn_points(start, dest, (CX, CY))
        v.set_path(path)
        self.moving_vehicles.append(v)
