import pygame
import math
import sys
import random
import threading
import socket
import sys

# --- Constants ---
PORT = 5000
BUFFER_SIZE = 100
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 800
ROAD_WIDTH = 150
LANE_WIDTH = 50

# --- Globals ---
current_light = 0 # 1=A, 2=B, 3=C, 4=D
next_light = 0
vehicle_queue = []
vehicle_queue_lock = threading.Lock()
active_vehicles = []
lock = threading.Lock()

# --- Classes ---

class Vehicle:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.speed = 2.0
        self.lane = 0
        self.path_option = 0
        self.body_color = (255, 255, 255)
        self.active = True
        self.horizontal = False
        
        # Turning State
        self.turning = False
        self.t = 0.0
        self.t_speed = 0.0
        self.p0 = (0,0)
        self.p1 = (0,0)
        self.p2 = (0,0)
        self.target_lane = 0
        self.target_horizontal = False

# --- Socket Server ---
def socket_receiver_thread():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind(('0.0.0.0', PORT))
        server.listen(3)
        print(f"Server listening on port {PORT}...")
        
        while True:
            conn, addr = server.accept()
            print("Client connected (Traffic Generator)...")
            with conn:
                buffer = ""
                while True:
                    data = conn.recv(1024)
                    if not data:
                        print("Client disconnected.")
                        break
                    
                    try:
                        buffer += data.decode('utf-8')
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if line.isdigit():
                                with vehicle_queue_lock:
                                    vehicle_queue.append(line)
                                print(f"Received: {line} (Queue: {len(vehicle_queue)})")
                    except Exception as e:
                        print(f"Error parsing socket data: {e}")

            print("Waiting for new connection...")
            
    except Exception as e:
        print(f"Socket Server Error: {e}")

# --- Helper Functions ---

def get_lane_angle(lane):
    if 1 <= lane <= 3: return 90.0
    if 4 <= lane <= 6: return 270.0
    if 7 <= lane <= 9: return 180.0
    return 0.0

# --- Visual Config ---
ROAD_COLOR = (40, 40, 40)
MARKING_COLOR = (200, 200, 200)
BG_COLOR = (30, 100, 30) # Grass Green
TEXT_COLOR = (255, 255, 255)

def spawn_vehicle(lane):
    if lane in [1, 6, 7, 12]:
        return

    v = Vehicle()
    v.active = True
    v.speed = 2.0
    v.path_option = random.randint(0, 1)
    
    # Neon/Pastel Colors
    colors = [
        (255, 100, 100), (100, 255, 100), (100, 100, 255),
        (255, 255, 100), (255, 100, 255), (100, 255, 255),
        (255, 150, 50), (50, 255, 150)
    ]
    v.body_color = random.choice(colors)
    v.turning = False
    v.t = 0.0
    
    center = WINDOW_WIDTH / 2.0
    road_half = ROAD_WIDTH / 2.0
    
    if 1 <= lane <= 3: # A (Top)
        sub = lane - 1
        carW = 25.0
        laneInnerOffset = (LANE_WIDTH - carW) / 2.0
        startX = center - road_half + laneInnerOffset
        v.x = startX + sub * LANE_WIDTH
        v.y = -50.0 # Start off-screen
        v.horizontal = False
        
    elif 4 <= lane <= 6: # B (Bot)
        sub = lane - 4
        carW = 25.0
        laneInnerOffset = (LANE_WIDTH - carW) / 2.0
        startX = center - road_half + laneInnerOffset
        v.x = startX + sub * LANE_WIDTH
        v.y = WINDOW_HEIGHT + 50.0
        v.horizontal = False
        
    elif 7 <= lane <= 9: # C (Right)
        sub = lane - 7
        carH = 25.0
        laneInnerOffset = (LANE_WIDTH - carH) / 2.0
        startY = center - road_half + laneInnerOffset
        v.y = startY + sub * LANE_WIDTH
        v.x = WINDOW_WIDTH + 50.0
        v.horizontal = True
        
    elif 10 <= lane <= 12: # D (Left)
        sub = lane - 10
        carH = 25.0
        laneInnerOffset = (LANE_WIDTH - carH) / 2.0
        startY = center - road_half + laneInnerOffset
        v.y = startY + sub * LANE_WIDTH
        v.x = -50.0
        v.horizontal = True
        
    else:
        return
        
    v.lane = lane
    active_vehicles.append(v)
    print(f"Spawned Vehicle: Lane {lane}, Pos ({v.x:.1f}, {v.y:.1f}), Color {v.body_color}")

# ... (Previous helper functions remain) ...

def count_vehicles_on_road(road_index):
    # 0=A, 1=B, 2=C, 3=D
    count = 0
    for v in active_vehicles:
        if not v.active or v.turning: continue
        
        if road_index == 0 and 1 <= v.lane <= 3:
            if v.y <= 295: count += 1
        elif road_index == 1 and 4 <= v.lane <= 6:
            if v.y >= 465: count += 1
        elif road_index == 2 and 7 <= v.lane <= 9:
            if v.x >= 465: count += 1
        elif road_index == 3 and 10 <= v.lane <= 12:
            if v.x <= 295: count += 1
    return count

def update_vehicles():
    global active_vehicles
    
    l_state = next_light
    
    lane_groups = {i: [] for i in range(1, 13)}
    for v in active_vehicles:
        if 1 <= v.lane <= 12:
            lane_groups[v.lane].append(v)
            
    # Sorters
    # A (1-3): Down (Increasing Y) -> Sort Y Asc
    # B (4-6): Up (Decreasing Y) -> Sort Y Desc
    # C (7-9): Left (Decreasing X) -> Sort X Desc
    # D (10-12): Right (Increasing X) -> Sort X Asc
    
    for l in range(1, 4): lane_groups[l].sort(key=lambda v: v.y, reverse=True)
    for l in range(4, 7): lane_groups[l].sort(key=lambda v: v.y)
    for l in range(7, 10): lane_groups[l].sort(key=lambda v: v.x)
    for l in range(10, 13): lane_groups[l].sort(key=lambda v: v.x, reverse=True)
    
    min_gap = 45.0
    
    def can_advance(v):
        # Stop Lines Check
        # A: y >= 280 && y <= 290 && Red
        if 1 <= v.lane <= 3 and 280 <= v.y <= 290 and l_state != 1: return False
        # B: y <= 480 && y >= 470 && Red
        if 4 <= v.lane <= 6 and 470 <= v.y <= 480 and l_state != 2: return False
        # C: x <= 480 && x >= 470 && Red
        if 7 <= v.lane <= 9 and 470 <= v.x <= 480 and l_state != 3: return False
        # D: x >= 280 && x <= 290 && Red
        if 10 <= v.lane <= 12 and 280 <= v.x <= 290 and l_state != 4: return False
        return True

    def start_turn(v, t_lane, t_horz, p1x, p1y, p2x, p2y):
        v.turning = True
        v.t = 0.0
        v.target_lane = t_lane
        v.target_horizontal = t_horz
        v.p0 = (v.x, v.y)
        v.p1 = (p1x, p1y)
        v.p2 = (p2x, p2y)
        
        dx = v.p0[0] - v.p2[0]
        dy = v.p0[1] - v.p2[1]
        dist = math.hypot(dx, dy)
        length = max(dist * 1.11, 1.0)
        
        v.t_speed = (v.speed * 0.6) / length

    # Move Vertical
    # Increasing Y (A: 1-3)
    for lane in range(1, 4):
        vec = lane_groups[lane]
        for i, v in enumerate(vec):
            if v.turning: continue
            if not can_advance(v): continue
            
            proposed = v.y + v.speed
            if i > 0:
                front = vec[i-1]
                if front.y - proposed < min_gap: continue
            v.y = proposed
            
            # Logic: Lane 3 Turn
            if v.lane == 3 and 307.5 <= v.y < 380.0:
                start_turn(v, 10, True, 437.5, 337.5, 487.5, 337.5)
            # Logic: Lane 2
            elif v.lane == 2:
                if v.path_option == 1 and 407.5 <= v.y <= 445.0:
                    start_turn(v, 9, True, 387.5, 437.5, 300.0, 437.5)
                elif v.path_option == 0 and 380.0 <= v.y <= 400.0:
                    start_turn(v, 3, False, 412.5, v.y+50, 437.5, v.y+100)

    # Decreasing Y (B: 4-6)
    for lane in range(4, 7):
        vec = lane_groups[lane]
        for i, v in enumerate(vec):
            if v.turning: continue
            if not can_advance(v): continue
            
            proposed = v.y - v.speed
            if i > 0:
                front = vec[i-1]
                if proposed - front.y < min_gap: continue
            v.y = proposed
            
            # Logic Lane 4 Turn
            if v.lane == 4 and 400.0 < v.y <= 467.5:
                start_turn(v, 9, True, 337.5, 437.5, 287.5, 437.5)
            # Logic Lane 5
            elif v.lane == 5:
                if v.path_option == 1 and 330.0 <= v.y <= 367.5:
                    start_turn(v, 10, True, 387.5, 337.5, 450.0, 337.5)
                elif v.path_option == 0 and 400.0 <= v.y <= 420.0:
                    start_turn(v, 4, False, 362.5, v.y-50, 337.5, v.y-100)

    # Move Horizontal
    # Decreasing X (C: 7-9)
    for lane in range(7, 10):
        vec = lane_groups[lane]
        for i, v in enumerate(vec):
            if v.turning: continue
            if not can_advance(v): continue
            
            proposed = v.x - v.speed
            if i > 0:
                front = vec[i-1]
                if proposed - front.x < min_gap: continue
            v.x = proposed
            
            # Logic Lane 9 Turn? C++ uses "moveHorizontal(7,9,false)".
            # In C++ moveHorizontal: lane 9 check
            if v.lane == 9 and 420.0 < v.x <= 467.5:
                start_turn(v, 3, False, 437.5, 437.5, 437.5, 517.5)
            # Logic Lane 8
            elif v.lane == 8:
                if v.path_option == 1 and 330.0 <= v.x <= 367.5:
                    start_turn(v, 4, False, 337.5, 387.5, 337.5, 270.0) # Weird Y coords? Copying C++
                elif v.path_option == 0 and 400.0 <= v.x <= 420.0:
                    start_turn(v, 9, False, v.x-50, 412.5, v.x-100, 437.5)

    # Increasing X (D: 10-12)
    for lane in range(10, 13):
        vec = lane_groups[lane]
        for i, v in enumerate(vec):
            if v.turning: continue
            if not can_advance(v): continue
            
            proposed = v.x + v.speed
            if i > 0:
                front = vec[i-1]
                if front.x - proposed < min_gap: continue
            v.x = proposed
            
            # Logic Lane 10
            if v.lane == 10 and 307.5 <= v.x < 380.0:
                start_turn(v, 4, False, 337.5, 337.5, 337.5, 257.5)
            # Logic Lane 11
            elif v.lane == 11:
                if v.path_option == 1 and 407.5 <= v.x <= 445.0:
                    start_turn(v, 3, False, 437.5, 387.5, 437.5, 530.0)
                elif v.path_option == 0 and 380.0 <= v.x <= 400.0:
                    start_turn(v, 10, False, v.x+50, 362.5, v.x+100, 337.5)

    # Turns Update
    for v in active_vehicles:
        if v.turning:
            v.t += v.t_speed
            if v.t >= 1.0:
                v.t = 1.0
                v.turning = False
                v.lane = v.target_lane
                v.horizontal = v.target_horizontal
                v.x = v.p2[0]
                v.y = v.p2[1]
            else:
                u = 1.0 - v.t
                tt = v.t * v.t
                uu = u * u
                v.x = uu * v.p0[0] + 2 * u * v.t * v.p1[0] + tt * v.p2[0]
                v.y = uu * v.p0[1] + 2 * u * v.t * v.p1[1] + tt * v.p2[1]

    # Remove OOB
    active_vehicles = [v for v in active_vehicles if -100 <= v.x <= 900 and -100 <= v.y <= 900]

def main():
    global current_light, next_light
    
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Traffic Simulator (Python Port)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)

    # Start Receiver
    t = threading.Thread(target=socket_receiver_thread, daemon=True)
    t.start()

    last_light_switch_time = pygame.time.get_ticks()
    light_phase = 1 # 1=A, 2=B...
    target_phase = 1
    is_transitioning = False
    priority_lane = -1
    
    running = True
    while running:
        clock.tick(60) # 16ms
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Process Queue
        with vehicle_queue_lock:
            while vehicle_queue:
                data = vehicle_queue.pop(0)
                try:
                    if data:
                        spawn_vehicle(int(data))
                except:
                    pass

        current_time = pygame.time.get_ticks()
        
        # Adaptive Logic
        if priority_lane == -1:
            for i in range(4):
                if count_vehicles_on_road(i) >= 6:
                    priority_lane = i
                    print(f"Priority mode activated for Road {chr(ord('A')+i)}")
                    break
        else:
            if count_vehicles_on_road(priority_lane) <= 3:
                print(f"Priority mode deactivated for Road {chr(ord('A')+priority_lane)}")
                priority_lane = -1
        
        if not is_transitioning:
            target_phase = light_phase
            if priority_lane != -1:
                if light_phase != priority_lane + 1:
                    target_phase = priority_lane + 1
            else:
                if current_time - last_light_switch_time > 3000:
                    found = False
                    for i in range(1, 5):
                        chk = (light_phase - 1 + i) % 4
                        if count_vehicles_on_road(chk) > 0:
                            target_phase = chk + 1
                            found = True
                            break
                    if not found:
                        target_phase = (light_phase % 4) + 1

        if light_phase != target_phase:
            if not is_transitioning:
                is_transitioning = True
                last_light_switch_time = current_time
                next_light = 0 # Yellow/All Red
            else:
                if current_time - last_light_switch_time > 1000:
                    light_phase = target_phase
                    next_light = light_phase
                    is_transitioning = False
                    last_light_switch_time = current_time
        else:
            if not is_transitioning:
                next_light = light_phase
                
        # Update Physics
        update_vehicles()
        if current_light != next_light:
            current_light = next_light
            print(f"Light state updated to {current_light}")

        # Render
        screen.fill(BG_COLOR)
        
        # Draw Roads (Dark Asphalt)
        center = WINDOW_WIDTH / 2.0
        road_half = ROAD_WIDTH / 2.0
        
        # Shadows / Borders
        pygame.draw.rect(screen, (30, 30, 30), (center - road_half - 2, 0, ROAD_WIDTH + 4, WINDOW_HEIGHT))
        pygame.draw.rect(screen, (30, 30, 30), (0, center - road_half - 2, WINDOW_WIDTH, ROAD_WIDTH + 4))

        # Pavement
        pygame.draw.rect(screen, ROAD_COLOR, (center - road_half, 0, ROAD_WIDTH, WINDOW_HEIGHT))
        pygame.draw.rect(screen, ROAD_COLOR, (0, center - road_half, WINDOW_WIDTH, ROAD_WIDTH))
        
        # Intersection Box (Clean)
        pygame.draw.rect(screen, ROAD_COLOR, (center - road_half, center - road_half, ROAD_WIDTH, ROAD_WIDTH))
        
        # Lane Dividers (Glowing White)
        lane_offset = float(LANE_WIDTH)
        
        # Function to draw dashed lines
        def draw_dashed_line(start, end, vertical=True):
            if vertical:
                x = start[0]
                y1, y2 = start[1], end[1]
                for y in range(int(y1), int(y2), 40):
                    if not (center - road_half < y < center + road_half):
                        pygame.draw.rect(screen, MARKING_COLOR, (x - 1, y, 2, 20))
            else:
                y = start[1]
                x1, x2 = start[0], end[0]
                for x in range(int(x1), int(x2), 40):
                    if not (center - road_half < x < center + road_half):
                        pygame.draw.rect(screen, MARKING_COLOR, (x, y - 1, 20, 2))

        # Vertical Dividers
        draw_dashed_line((center - road_half + LANE_WIDTH, 0), (center - road_half + LANE_WIDTH, WINDOW_HEIGHT))
        draw_dashed_line((center - road_half + LANE_WIDTH*2, 0), (center - road_half + LANE_WIDTH*2, WINDOW_HEIGHT))
        
        # Horizontal Dividers
        draw_dashed_line((0, center - road_half + LANE_WIDTH), (WINDOW_WIDTH, center - road_half + LANE_WIDTH), False)
        draw_dashed_line((0, center - road_half + LANE_WIDTH*2), (WINDOW_WIDTH, center - road_half + LANE_WIDTH*2), False)

        # Crosswalks (Subtle)
        cw_w = ROAD_WIDTH
        cw_h = 20
        col = (60, 60, 60)
        # Top
        pygame.draw.rect(screen, col, (center - road_half, center - road_half - cw_h, cw_w, cw_h), 2)
        # Bot
        pygame.draw.rect(screen, col, (center - road_half, center + road_half, cw_w, cw_h), 2)
        # Left
        pygame.draw.rect(screen, col, (center - road_half - cw_h, center - road_half, cw_h, cw_w), 2)
        # Right
        pygame.draw.rect(screen, col, (center + road_half, center - road_half, cw_h, cw_w), 2)
        
        # Traffic Lights (Sleek)
        def draw_light(x, y, is_red, horz):
            w = 40 if horz else 20
            h = 20 if horz else 40
            pygame.draw.rect(screen, (30, 30, 35), (x, y, w, h), border_radius=4)
            
            # Glow Effect
            glow_idx = 0 if is_red else 1
            colors = [(255, 50, 50), (50, 255, 50)]
            
            # Red
            r_col = colors[0] if is_red else (80, 20, 20)
            rx = x + 5
            ry = y + 5
            pygame.draw.circle(screen, r_col, (rx + 5, ry + 5), 5)
            
            # Green
            g_col = colors[1] if not is_red else (20, 80, 20)
            gx = x + 5 + (20 if horz else 0)
            gy = y + 5 + (0 if horz else 20)
            pygame.draw.circle(screen, g_col, (gx + 5, gy + 5), 5)

        l_state = next_light
        # Lights at corners (Right-side relative to driver)
        draw_light(295, 275, l_state != 1, False) # A (Top-Left)
        draw_light(485, 485, l_state != 2, False) # B (Bot-Right)
        draw_light(485, 275, l_state != 3, False) # C (Top-Right)
        draw_light(295, 485, l_state != 4, False) # D (Bot-Left)
        
        # Vehicles
        for v in active_vehicles:
            if not v.active: continue
            
            # Angle Logic
            # Angle Logic
            if v.turning:
                # Calculate Bezier derivative (tangent) for fluid rotation
                t = v.t
                dx = 2 * (1 - t) * (v.p1[0] - v.p0[0]) + 2 * t * (v.p2[0] - v.p1[0])
                dy = 2 * (1 - t) * (v.p1[1] - v.p0[1]) + 2 * t * (v.p2[1] - v.p1[1])
                render_angle = math.degrees(math.atan2(dy, dx))
            else:
                render_angle = get_lane_angle(v.lane)
            
            # Draw
            cx = v.x + (20.0 if v.horizontal else 12.5)
            cy = v.y + (12.5 if v.horizontal else 20.0)
            
            # Car Body
            surf = pygame.Surface((40, 25), pygame.SRCALPHA)
            pygame.draw.rect(surf, v.body_color, (0, 0, 40, 25), border_radius=6)

            # Rotate
            rotated = pygame.transform.rotate(surf, -render_angle)
            rect = rotated.get_rect(center=(cx, cy))
            screen.blit(rotated, rect)

        # Draw Mode Indicator
        mode_text = "MODE: NORMAL"
        mode_color = (255, 255, 255) 

        if priority_lane != -1:
            mode_text = f"MODE: PRIORITY (Road {chr(ord('A') + priority_lane)})"
            mode_color = (255, 200, 50) # Orange/Gold

        # Draw text with a slight shadow for better readability
        shadow_surf = font.render(mode_text, True, (0, 0, 0))
        screen.blit(shadow_surf, (12, 12))
        
        mode_surf = font.render(mode_text, True, mode_color)
        screen.blit(mode_surf, (10, 10))



        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
