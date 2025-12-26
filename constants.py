import pygame

# Screen & Game Settings
WIDTH, HEIGHT = 800, 800
FPS = 60
TITLE = "Traffic Junction Simulator - Assignment 1"

# Colors
GRASS_GREEN = (30, 100, 30)   # Darker green for realism
ROAD_GRAY = (50, 50, 50)
WHITE = (255, 255, 255)
YELLOW = (255, 215, 0)
RED = (255, 69, 0)
GREEN = (50, 205, 50)
BLUE = (100, 149, 237)

# Vehicle Settings
VEHICLE_W, VEHICLE_H = 20, 30
VEHICLE_SPEED = 3

# Logic Constants
PRIORITY_START = 10
PRIORITY_STOP = 5
VEHICLE_PASS_TIME = 2.0

# Coordinates for Stop Lines (Where cars wait)
STOP_LINE_A = 300 # Y coordinate
STOP_LINE_B = 500 # Y coordinate
STOP_LINE_C = 500 # X coordinate (Right side)
STOP_LINE_D = 300 # X coordinate (Left side)