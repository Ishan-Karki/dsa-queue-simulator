import math
import heapq

# --- Configuration Constants ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 900
FPS = 60

# Physics
MAX_SPEED = 2.5
ACCELERATION = 0.1
BRAKE_FORCE = 0.2
TURN_SPEED = 1.5

# Socket Config
HOST = 'localhost'
PORT = 5000
BUFFER_SIZE = 1024

# Dimensions
LANE_WIDTH = 40
LANE_COUNT_ONE_WAY = 3
INTERSECTION_SIZE = LANE_COUNT_ONE_WAY * LANE_WIDTH * 2 # 240px (3 In + 3 Out)

CX, CY = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

# Lane Offsets relative to center
# Incoming (Approaching intersection): On the Left side (LHT - Nepal/UK)
# Lane 1 (Divider side? or Curb side?)
# Usually: L3 (Left Turn) is Curb side. L1/L2 are Center.
# Let's map: 
# Center Line -> | L1 | L2 | L3 | -> Curb
# This creates conflict if L3 is "Left Turn" (Free Left). 
# In LHT, Left Turn is the Curb side. Correct.
# So order from Center: L1, L2, L3.

class Utils:
    @staticmethod
    def get_turn_points(start, end, control):
        points = []
        for t in range(0, 51): # 50 steps
            t /= 50.0
            x = (1-t)**2 * start[0] + 2*(1-t)*t * control[0] + t**2 * end[0]
            y = (1-t)**2 * start[1] + 2*(1-t)*t * control[1] + t**2 * end[1]
            points.append((x, y))
        return points
