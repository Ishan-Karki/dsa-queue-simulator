import pygame
import os
from constants import *
from data_structures import LaneQueue, Vehicle
from logic_engine import TrafficController

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18, bold=True)

# --- SETUP LANES ---
lanes = {}
for r in ['A', 'B', 'C', 'D']:
    for i in range(1, 4):
        lanes[f"{r}L{i}"] = LaneQueue(f"{r}L{i}")

controller = TrafficController()
all_vehicles = [] # List to track all active vehicle objects for drawing

# --- SPAWN COORDINATE CALCULATOR ---
def get_spawn_pos(lane_id):
    road = lane_id[0]
    lane_num = int(lane_id[2])
    
    # Offsets to place cars in correct lane (1, 2, 3)
    # Road A (Top): Lane 1 is outer left, Lane 3 is inner right (relative to driving side)
    # We assume Right Hand Traffic for visual clarity:
    # A (Top) drives Down on the LEFT side of screen? No, Right Hand Traffic means Right side.
    # Let's map strictly to the Diagram provided (Figure 1):
    # A (Top): Incoming is on the LEFT side of the vertical road.
    
    offset_1 = 30 # Lane 1 (Outer)
    offset_2 = 55 # Lane 2 (Middle)
    offset_3 = 80 # Lane 3 (Inner/Free)
    
    if road == 'A': # Spawns Top, Moves Down
        x = (WIDTH // 2) - [0, 80, 55, 30][lane_num] 
        return (x, -50, 0, 1)
    elif road == 'B': # Spawns Bottom, Moves Up
        x = (WIDTH // 2) + [0, 80, 55, 30][lane_num]
        return (x, HEIGHT + 50, 0, -1)
    elif road == 'D': # Spawns Left, Moves Right
        y = (HEIGHT // 2) + [0, 80, 55, 30][lane_num]
        return (-50, y, 1, 0)
    elif road == 'C': # Spawns Right, Moves Left
        y = (HEIGHT // 2) - [0, 80, 55, 30][lane_num]
        return (WIDTH + 50, y, -1, 0)
    return (0, 0, 0, 0)

# --- FILE POLLING ---
def poll_traffic_files():
    for r in ['a', 'b', 'c', 'd']:
        fname = f"lane{r}.txt"
        if os.path.exists(fname):
            try:
                with open(fname, 'r') as f:
                    lines = f.readlines()
                # Clear file
                with open(fname, 'w') as f:
                    f.write("")
                
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    # Construct ID (e.g., AL1)
                    full_id = f"{r.upper()}{line}" 
                    if full_id in lanes:
                        x, y, dx, dy = get_spawn_pos(full_id)
                        v = Vehicle(full_id, x, y, dx, dy)
                        # Set color based on lane
                        if '3' in full_id: v.color = BLUE # Free lane
                        elif '2' in full_id: v.color = (255, 165, 0) # Priority/Light lane
                        
                        lanes[full_id].enqueue(v)
                        all_vehicles.append(v)
            except:
                pass

# --- DRAWING HELPERS ---
def draw_road_markings():
    # Draw Asphalt
    pygame.draw.rect(screen, ROAD_GRAY, (WIDTH//2 - 100, 0, 200, HEIGHT)) # Vertical
    pygame.draw.rect(screen, ROAD_GRAY, (0, HEIGHT//2 - 100, WIDTH, 200)) # Horizontal
    
    # Draw Center Yellow Lines
    pygame.draw.line(screen, YELLOW, (WIDTH//2, 0), (WIDTH//2, HEIGHT), 3)
    pygame.draw.line(screen, YELLOW, (0, HEIGHT//2), (WIDTH, HEIGHT//2), 3)
    
    # Draw Stop Lines (White)
    pygame.draw.line(screen, WHITE, (WIDTH//2 - 100, STOP_LINE_A), (WIDTH//2, STOP_LINE_A), 5) # A
    pygame.draw.line(screen, WHITE, (WIDTH//2, STOP_LINE_B), (WIDTH//2 + 100, STOP_LINE_B), 5) # B
    pygame.draw.line(screen, WHITE, (STOP_LINE_D, HEIGHT//2), (STOP_LINE_D, HEIGHT//2 + 100), 5) # D
    pygame.draw.line(screen, WHITE, (STOP_LINE_C, HEIGHT//2 - 100), (STOP_LINE_C, HEIGHT//2), 5) # C

def draw_lights():
    # Positions for lights relative to stop lines
    # Road A Light (Top Left quadrant)
    color_a = GREEN if controller.current_green_road == 'A' else RED
    pygame.draw.circle(screen, color_a, (WIDTH//2 - 20, STOP_LINE_A + 20), 15)
    
    # Road B Light (Bottom Right quadrant)
    color_b = GREEN if controller.current_green_road == 'B' else RED
    pygame.draw.circle(screen, color_b, (WIDTH//2 + 20, STOP_LINE_B - 20), 15)
    
    # Road D Light (Bottom Left quadrant)
    color_d = GREEN if controller.current_green_road == 'D' else RED
    pygame.draw.circle(screen, color_d, (STOP_LINE_D + 20, HEIGHT//2 + 20), 15)
    
    # Road C Light (Top Right quadrant)
    color_c = GREEN if controller.current_green_road == 'C' else RED
    pygame.draw.circle(screen, color_c, (STOP_LINE_C - 20, HEIGHT//2 - 20), 15)

# --- MAIN LOOP ---
running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    
    # 1. Inputs & Polling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    poll_traffic_files()
    
    # 2. Logic Update
    controller.update(lanes, dt)
    
    # 3. Vehicle Logic (Stop/Go)
    for v in all_vehicles[:]:
        road = v.lane_id[0]
        lane_num = v.lane_id[2]
        
        # Determine if should stop
        should_stop = False
        
        # [cite_start]Rule: Lane 3 is FREE (Never stops) [cite: 20]
        if lane_num != '3':
            is_green = (controller.current_green_road == road)
            
            # Check proximity to stop line
            if road == 'A' and (v.y > STOP_LINE_A - 40 and v.y < STOP_LINE_A) and not is_green: should_stop = True
            elif road == 'B' and (v.y < STOP_LINE_B + 10 and v.y > STOP_LINE_B) and not is_green: should_stop = True
            elif road == 'D' and (v.x > STOP_LINE_D - 40 and v.x < STOP_LINE_D) and not is_green: should_stop = True
            elif road == 'C' and (v.x < STOP_LINE_C + 10 and v.x > STOP_LINE_C) and not is_green: should_stop = True
            
        # Move if not stopped
        speed = 0 if should_stop else VEHICLE_SPEED
        v.move(speed)
        
        # Cleanup if off screen
        if v.x < -100 or v.x > WIDTH + 100 or v.y < -100 or v.y > HEIGHT + 100:
            all_vehicles.remove(v)
            lanes[v.lane_id].dequeue()

    # 4. Drawing
    screen.fill(GRASS_GREEN)
    draw_road_markings()
    draw_lights()
    
    # Draw Vehicles
    for v in all_vehicles:
        v.draw(screen)
        
    # UI Overlay
    info_text = f"Green Road: {controller.current_green_road} | AL2 Count: {lanes['AL2'].count()}"
    p_text = "PRIORITY MODE ACTIVE" if controller.is_priority_mode else "Normal Mode"
    screen.blit(font.render(info_text, True, WHITE), (10, 10))
    screen.blit(font.render(p_text, True, YELLOW if controller.is_priority_mode else WHITE), (10, 35))

    pygame.display.flip()

pygame.quit()