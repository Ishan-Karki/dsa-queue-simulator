import random
import math
import pygame
import heapq
from utils import *

# --- State Machine Definitions ---
STATE_1 = 'STATE_1'   # Stop/Red
STATE_2 = 'STATE_2'   # Go/Green

class LaneQueue:
    """Queue implementation using a Python list (simulating a linear array)"""
    def __init__(self):
        self._queue = []

    def enqueue(self, vehicle):
        self._queue.append(vehicle)

    def dequeue(self):
        if self._queue:
            return self._queue.pop(0)
        return None

    def __len__(self):
        return len(self._queue)

    def __iter__(self):
        return iter(self._queue)

    def __getitem__(self, index):
        return self._queue[index]

class TrafficLight:
    def __init__(self):
        self.state = STATE_1 # Default to State 1 (Red/Stop)

class Vehicle:
    def __init__(self, v_id, lane, x=0, y=0):
        self.id = v_id
        self.lane = lane
        self.x = x
        self.y = y
        self.angle = 0
        self.path = []
        self.path_index = 0
        self.state = 'QUEUED' # QUEUED, STOPPED, MOVING
        
        # Init physics
        self.speed = 0
        
        # Color based on lane: ONLY AL2 is Priority Blue. Others are random.
        if lane.road_id == 'A' and lane.name == 'L2':
            self.color = (50, 100, 255) # Priority Blue
        else:
            # Standard Palette: Red, Grey, Silver, Orange, Yellow
            palette = [
                (200, 50, 50),   # Muted Red
                (180, 180, 190), # Silver
                (220, 220, 230), # Light Grey
                (255, 140, 0),   # Orange
                (255, 200, 50),  # Yellow
                (100, 100, 110)  # Dark Grey
            ]
            self.color = random.choice(palette)

    def set_path(self, path):
        self.path = path
        self.state = 'MOVING'
        # Removed self.x, self.y = path[0] to prevent teleportation popping

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
            
            # Move at constant MAX_SPEED
            self.angle = math.atan2(dy, dx)
            
            # Ensure we don't overstep the target
            move_dist = min(dist, MAX_SPEED)
            self.x += math.cos(self.angle) * move_dist
            self.y += math.sin(self.angle) * move_dist

class Lane:
    def __init__(self, name, road_id):
        self.name = name # L1, L2, L3
        self.road_id = road_id
        self.road_id = road_id
        self.vehicles = LaneQueue()
        self.stop_pos = (0,0) # To be set by Intersection

class Road:
    def __init__(self, r_id):
        self.id = r_id
        self.L1 = Lane('L1', r_id) # Incoming
        self.L2 = Lane('L2', r_id) # Middle Lane (Priority for A only)
        self.L3 = Lane('L3', r_id) # Free Left
        self.lanes = [self.L1, self.L2, self.L3]
        self.main_light = TrafficLight()
        
    def get_waiting_lanes_count(self):
        # Count vehicles waiting in L1, L2, and L3 (as per n=3 in formula)
        return len(self.L1.vehicles), len(self.L2.vehicles), len(self.L3.vehicles)

class Intersection:
    def __init__(self):
        self.roads = {
            'A': Road('A'), 'B': Road('B'), 'C': Road('C'), 'D': Road('D')
        }
        self.timer = 0
        self.green_duration = 600 # Initial 10s
        self.current_green_idx = 0 # 0=A,1=B,2=C,3=D
        self.order = ['A', 'B', 'C', 'D']
        self.priority_mode = False
        self.p_road = None
        
        # Priority Queue for road service order
        self.service_pq = [] # Max-Heap of (-count, road_id)
        
        self.dispatch_timer = 0
        self.dispatch_interval = 30 # Frames between dispatches (0.5s at 60fps)
        self.moving_vehicles = []
        
        self._setup_coordinates()

    def add_vehicle(self, r_id, l_id):
        if r_id in self.roads:
            lane = getattr(self.roads[r_id], l_id)
            v_id = f"{r_id}{l_id}_{random.randint(1000,9999)}"
            
            # Spawn at far end (Off-screen)
            offsets = {'L1': -0.5*LANE_WIDTH, 'L2': -1.5*LANE_WIDTH, 'L3': -1.5*LANE_WIDTH}
            off = offsets[l_id]
            if r_id == 'A': x, y = CX + off, -50
            elif r_id == 'C': x, y = CX - off, SCREEN_HEIGHT + 50
            elif r_id == 'B': x, y = SCREEN_WIDTH + 50, CY + off
            elif r_id == 'D': x, y = -50, CY - off
            
            lane.vehicles.enqueue(Vehicle(v_id, lane, x, y))

    def _setup_coordinates(self):
        half = INTERSECTION_SIZE // 2
        
        # A (Top)
        self.roads['A'].L1.stop_pos = (CX - 0.5*LANE_WIDTH, CY - half)
        self.roads['A'].L2.stop_pos = (CX - 1.5*LANE_WIDTH, CY - half)
        self.roads['A'].L3.stop_pos = (CX - 1.5*LANE_WIDTH, CY - half) # Clamped to L2
        
        # B (Right)
        self.roads['B'].L1.stop_pos = (CX + half, CY - 0.5*LANE_WIDTH)
        self.roads['B'].L2.stop_pos = (CX + half, CY - 1.5*LANE_WIDTH)
        self.roads['B'].L3.stop_pos = (CX + half, CY - 1.5*LANE_WIDTH) # Clamped
        
        # C (Bottom)
        self.roads['C'].L1.stop_pos = (CX + 0.5*LANE_WIDTH, CY + half)
        self.roads['C'].L2.stop_pos = (CX + 1.5*LANE_WIDTH, CY + half)
        self.roads['C'].L3.stop_pos = (CX + 1.5*LANE_WIDTH, CY + half) # Clamped
        
        # D (Left)
        self.roads['D'].L1.stop_pos = (CX - half, CY + 0.5*LANE_WIDTH)
        self.roads['D'].L2.stop_pos = (CX - half, CY + 1.5*LANE_WIDTH)
        self.roads['D'].L3.stop_pos = (CX - half, CY + 1.5*LANE_WIDTH) # Clamped

    def update(self):
        # 1. Check Priority Condition (AL2 > 10)
        al2_count = len(self.roads['A'].L2.vehicles)
        
        if not self.priority_mode:
            if al2_count > 10:
                self.priority_mode = True
                self.p_road = 'A'
                self._log_priority_switch(True, al2_count)
        else:
            if al2_count < 5:
                self.priority_mode = False
                self.p_road = None
                self.timer = 0 
                self._log_priority_switch(False, al2_count)

        # 1.5 Update Queued Vehicle Positions (Movement to stop line)
        for r in self.roads.values():
            for l in [r.L1, r.L2, r.L3]:
                sx, sy = l.stop_pos
                gap = 25
                for i, v in enumerate(l.vehicles):
                    # Target position in queue
                    if r.id == 'A': tx, ty = sx, sy - (i+1)*gap
                    elif r.id == 'C': tx, ty = sx, sy + (i+1)*gap
                    elif r.id == 'B': tx, ty = sx + (i+1)*gap, sy
                    elif r.id == 'D': tx, ty = sx - (i+1)*gap, sy
                    
                    dx, dy = tx - v.x, ty - v.y
                    dist = math.hypot(dx, dy)
                    if dist > 1:
                        angle = math.atan2(dy, dx)
                        v.x += math.cos(angle) * MAX_SPEED
                        v.y += math.sin(angle) * MAX_SPEED
                        v.angle = angle
                    else:
                        v.x, v.y = tx, ty

        # 2. Update Lights based on Mode
        if self.priority_mode:
            self._set_lights(self.p_road)
        else:
            self.timer += 1
            if self.timer > self.green_duration:
                self.timer = 0
                
                # REBUILD PQ based on wait counts (Sum of all 3 lanes)
                self.service_pq = []
                for rid, road in self.roads.items():
                    l1, l2, l3 = road.get_waiting_lanes_count()
                    # Priority is total waiting length
                    heapq.heappush(self.service_pq, (-(l1 + l2 + l3), rid))
                
                # Get best road
                _, next_road_id = heapq.heappop(self.service_pq)
                self.current_road_id = next_road_id
                
                # Calculate Duration: |V| = 1/n * sum(|Li|) where n=3
                r_obj = self.roads[next_road_id]
                l1, l2, l3 = r_obj.get_waiting_lanes_count()
                v_avg = (l1 + l2 + l3) / 3.0
                
                t = 40 
                self.green_duration = max(600, int(v_avg * t))
                self.green_duration = min(self.green_duration, 1200)
                
            curr_id = self.order[self.current_green_idx]
            self._set_lights(curr_id)

        # 3. Dispatch Vehicles (Simulation Step)
        self._fair_dispatch()

    def _log_priority_switch(self, entered, count):
        mode_str = "PRIORITY" if entered else "NORMAL"
        msg = f">>> Switching to {mode_str} MODE (AL2 Count: {count}) <<<"
        print(msg)
        with open("traffic_logic.log", "a") as f:
            f.write(f"{pygame.time.get_ticks()}: {msg}\n")

    def _set_lights(self, green_road_id):
        for r_id, road in self.roads.items():
            state = STATE_2 if r_id == green_road_id else STATE_1
            road.main_light.state = state

    def _fair_dispatch(self):
        # Serve vehicles sequentially from GREEN roads with a fixed interval
        self.dispatch_timer += 1
        
        # 1. Handle Free Left (L3) - Can always go if clear
        for r in self.roads.values():
            if r.L3.vehicles and self.dispatch_timer >= self.dispatch_interval:
                # Random chance or simplified check for free left to avoid excessive clumping
                if random.random() < 0.1: 
                    v = r.L3.vehicles.dequeue()
                    self._route_vehicle(v, r.L3)
                    self.dispatch_timer = 0

        # 2. Handle Main Lanes (L1, L2) - Only if Main Light is GO
        if self.dispatch_timer >= self.dispatch_interval:
            for r in self.roads.values():
                if r.main_light.state == STATE_2:
                    # Serve L1 then L2 (Sequential Lane order)
                    v = None
                    if r.L1.vehicles:
                        v = r.L1.vehicles.dequeue()
                        l_obj = r.L1
                    elif r.L2.vehicles:
                        v = r.L2.vehicles.dequeue()
                        l_obj = r.L2
                    
                    if v:
                        self._route_vehicle(v, l_obj)
                        self.dispatch_timer = 0
                        break # Dispatch one per road/frame to maintain sequence

    def _route_vehicle(self, v, lane):
        start = lane.stop_pos
        rid = lane.road_id
        
        if lane.name == 'L3':
            target_map = {'A': 'B', 'B': 'C', 'C': 'D', 'D': 'A'}
            d_id = target_map[rid]
        else:
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
