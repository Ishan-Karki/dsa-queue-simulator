import socket
import time
import random
import threading
import sys
import queue

# --- Constants ---
HOST = '127.0.0.1'
PORT = 5000

# --- Classes ---
class Vehicle:
    def __init__(self, lane, road):
        self.lane = lane
        self.road = road
        self.id = id(self)

class VehicleQueue:
    def __init__(self, road_id):
        self.q = queue.Queue()
        self.road_id = road_id
        
    def enqueue(self, v):
        self.q.put(v)
        
    def count_lane(self, lane):
        # Allow checking internal queue for specific lane count
        # Not thread-safe strictly but okay for approximation
        c = 0
        for v in list(self.q.queue):
            if v.lane == lane: c += 1
        return c
        
    def dequeue_lane(self, lane):
        # Extract specific lane vehicle
        # Rebuild queue
        temp = []
        found = None
        while not self.q.empty():
            item = self.q.get()
            if found is None and item.lane == lane:
                found = item
            else:
                temp.append(item)
        for i in temp:
            self.q.put(i)
        return found
        
    def dequeue(self):
        if not self.q.empty():
            return self.q.get()
        return None
        
    def is_empty(self):
        return self.q.empty()
        
    def size(self):
        return self.q.qsize()

# --- Globals ---
road_queues = [VehicleQueue(0), VehicleQueue(1), VehicleQueue(2), VehicleQueue(3)] # A, B, C, D

def get_road_from_lane(lane):
    if 1 <= lane <= 3: return 0
    if 4 <= lane <= 6: return 1
    if 7 <= lane <= 9: return 2
    if 10 <= lane <= 12: return 3
    return -1

def get_queue(lane):
    r_id = get_road_from_lane(lane)
    if r_id != -1: return road_queues[r_id]
    return None

def main():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        print("Connected to server (Simulator)...")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    print("Queue-based vehicle generation system initialized.")
    
    # Speed Input
    speed_level = 3

    
    def generator_loop():
        while True:
            # Weighted Random Selection
            # 60% chance for AL2 (Lane 2), 40% spread among others
            if random.random() < 0.6:
                lane = 2
            else:
                # Other valid lanes excluding 2
                others = [3, 4, 5, 8, 9, 10, 11]
                lane = random.choice(others)
            
            road = get_road_from_lane(lane)
            v = Vehicle(lane, road)
            
            q = road_queues[road]
            q.enqueue(v)
            print(f"Generated vehicle for Road {chr(ord('A')+road)} Lane {lane}")
            
            # Dynamic Delay for Priority Buildup
            if lane == 2:
                # Faster bursts for AL2 to trigger priority
                delay = random.uniform(0.3, 0.6)
            else:
                # Slower, efficient traffic for others
                delay = random.uniform(0.8, 1.3)
                
            time.sleep(delay)

    t = threading.Thread(target=generator_loop, daemon=True)
    t.start()
    
    priority_mode = False
    
    while True:
        try:
            # Priority Logic (AL2 > 10)
            # AL2 is Road A (0), Lane 2
            a_q = road_queues[0]
            al2_count = a_q.count_lane(2)
            
            if al2_count > 10:
                priority_mode = True
            elif al2_count < 5:
                priority_mode = False
                
            sent = False
            
            if priority_mode and al2_count >= 5:
                v = a_q.dequeue_lane(2)
                if v:
                    try:
                        sock.sendall((str(v.lane) + "\n").encode())
                        print(f"PRIORITY: Sent AL2. Rem: {a_q.count_lane(2)}")
                        sent = True
                    except:
                        pass
            
            if not sent:
                # Round Robin
                for i in range(4):
                    q = road_queues[i]
                    if not q.is_empty():
                        v = q.dequeue()
                        if v:
                            try:
                                sock.sendall((str(v.lane) + "\n").encode())
                                print(f"Sent Road {chr(ord('A')+i)} Lane {v.lane}")
                                sent = True
                                break 
                            except:
                                pass
            
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error in send loop: {e}")
            break

if __name__ == "__main__":
    main()
