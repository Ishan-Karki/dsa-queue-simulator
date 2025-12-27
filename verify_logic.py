import sys
import os
import time

# Mock pygame for headless test
class MockPygame:
    class time:
        @staticmethod
        def get_ticks():
            return int(time.time() * 1000)

import builtins
builtins.pygame = MockPygame

from simulation import Intersection, Vehicle, LaneQueue
import random

def test_logic():
    print("Starting Headless Traffic Logic Test...")
    sim = Intersection()
    
    # 1. Test LaneQueue
    print("Testing LaneQueue...")
    q = LaneQueue()
    v1 = Vehicle("v1", None)
    q.enqueue(v1)
    if len(q) == 1 and q.dequeue() == v1 and len(q) == 0:
        print("LaneQueue: SUCCESS")
    else:
        print("LaneQueue: FAILED")
    
    # 2. Test 10/5 Rule
    print("Testing 10/5 Rule...")
    # Add 11 vehicles to AL2 to trigger priority
    for i in range(11):
        sim.add_vehicle('A', 'L2')
    
    sim.update()
    if sim.priority_mode == True and sim.p_road == 'A':
        print("Priority Entry (AL2 > 10): SUCCESS")
    else:
        print(f"Priority Entry: FAILED (Mode: {sim.priority_mode}, Road: {sim.p_road})")
    
    # Serve until AL2 < 5
    while len(sim.roads['A'].L2.vehicles) >= 5:
        sim.roads['A'].L2.vehicles.dequeue()
        sim.update()
    
    if sim.priority_mode == False:
        print("Priority Exit (AL2 < 5): SUCCESS")
    else:
        print("Priority Exit: FAILED")
    
    # 3. Test Free Left (Lane 3)
    print("Testing Free Left (Lane 3)...")
    sim.add_vehicle('B', 'L3')
    found = False
    for _ in range(200): # More attempts due to random probability
        sim.update()
        if len(sim.roads['B'].L3.vehicles) == 0:
            found = True
            break
    if found:
        print("Free Left Dispatch: SUCCESS")
    else:
        print("Free Left Dispatch: FAILED")

if __name__ == "__main__":
    test_logic()
