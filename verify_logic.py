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
    mock_lane = type('MockLane', (), {'name': 'L1'})()
    v1 = Vehicle("v1", mock_lane)
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

    # 4. Test Average Green Duration Calculation
    print("Testing Average Green Duration Logic...")
    sim2 = Intersection()
    # Path: AL1 (60), AL2 (0) -> Sum 60, Avg 30. Duration: 30 * 40 = 1200.
    # We use AL1 only to avoid triggering priority mode (which triggers on AL2 > 10)
    for i in range(60):
        sim2.add_vehicle('A', 'L1')
    
    # Trigger green for A
    sim2.current_green_idx = 3 # Previous was D, next is A
    sim2.timer = sim2.green_duration + 1 # Force switch
    sim2.update()
    
    expected_duration = int(((60 + 0) / 2.0) * 40)
    if sim2.green_duration == expected_duration:
        print(f"Average Duration Logic: SUCCESS (Duration: {sim2.green_duration})")
    else:
        print(f"Average Duration Logic: FAILED (Got: {sim2.green_duration}, Expected: {expected_duration})")

    # 5. Test Priority Queue Road Service
    print("Testing Priority Queue Road Service...")
    sim3 = Intersection()
    # Add most vehicles to Road C
    for _ in range(10): 
        sim3.add_vehicle('C', 'L1')
    # Add fewer to Road B
    for _ in range(5):
        sim3.add_vehicle('B', 'L1')
    
    # Trigger cycle end
    sim3.timer = sim3.green_duration + 1
    sim3.update()
    
    # Road C should be next (index 2 in order ['A', 'B', 'C', 'D'])
    if sim3.current_green_idx == 2:
        print("Priority Queue Road Service: SUCCESS (Road C prioritized)")
    else:
        print(f"Priority Queue Road Service: FAILED (Got index {sim3.current_green_idx}, Expected 2)")

    # 6. Test State Machine Constants
    print("Testing State Machine Constants...")
    from simulation import STATE_1, STATE_2
    if sim3.roads['A'].main_light.state in [STATE_1, STATE_2]:
        print(f"State Machine: SUCCESS (Current State: {sim3.roads['A'].main_light.state})")
    else:
        print(f"State Machine: FAILED (Unknown State: {sim3.roads['A'].main_light.state})")

if __name__ == "__main__":
    test_logic()
