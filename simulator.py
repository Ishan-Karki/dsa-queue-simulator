import pygame
import time
import os
import math
from data_structures import Lane, Vehicle, LaneType
from logic_engine import LogicEngine, TrafficLightState
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, RED, GREEN, GRAY, BLACK, WHITE, YELLOW,
    BLUE, DARK_GRAY, LIGHT_GRAY, DARK_GREEN, ROAD_GRAY, VEHICLE_BLUE, VEHICLE_GREEN,
    ROAD_A, ROAD_B, ROAD_C, ROAD_D, TIME_PER_VEHICLE
)


class VisualVehicle:
    """Represents a vehicle in the visualization."""
    
    def __init__(self, vehicle_id, road_id, lane_id, position, color=None):
        self.vehicle_id = vehicle_id
        self.road_id = road_id
        self.lane_id = lane_id
        self.position = position  # (x, y)
        self.color = color or BLUE
        self.width = 16  # Vehicle width (along direction of travel)
        self.height = 10  # Vehicle height (perpendicular to direction)
        self.speed = 2.0  # pixels per frame
        
        # For curved paths (L3 free lane)
        self.turning = False
        self.turn_progress = 0.0  # 0.0 to 1.0
        self.turn_radius = 50  # Radius for left turn curve
        self.start_turn_pos = None
        self.target_lane_center = None
    
    def draw(self, screen):
        """Draw the vehicle as a small colored rectangle."""
        x, y = self.position
        
        # Draw vehicle as a rectangle oriented along its direction
        # For now, draw as a simple rectangle (can be enhanced with rotation)
        pygame.draw.rect(screen, self.color, 
                        (x - self.width//2, y - self.height//2, self.width, self.height))
        pygame.draw.rect(screen, BLACK, 
                        (x - self.width//2, y - self.height//2, self.width, self.height), 1)


class TrafficSimulator:
    """Pygame-based traffic junction simulator."""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Traffic Junction Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Initialize logic engine
        self.logic_engine = LogicEngine(time_per_vehicle=TIME_PER_VEHICLE)
        
        # Track which vehicles have been processed from files
        self.processed_vehicle_indices = {
            ROAD_A: 0,
            ROAD_B: 0,
            ROAD_C: 0,
            ROAD_D: 0
        }
        
        # Visual vehicles on screen
        self.visual_vehicles = []
        self.vehicle_counter = 0
        
        # Junction layout parameters
        self.junction_center_x = SCREEN_WIDTH // 2
        self.junction_center_y = SCREEN_HEIGHT // 2
        self.road_width = 200
        self.lane_width = self.road_width // 3  # 3 lanes per road
        self.junction_size = 300
        
        # Road directions (from center)
        # Road A: Top (North)
        # Road B: Right (East)
        # Road C: Bottom (South)
        # Road D: Left (West)
        
        self.running = True
        self.last_file_poll_time = time.time()
        self.file_poll_interval = 0.5  # Poll files every 0.5 seconds
    
    def poll_lane_files(self):
        """Poll the lane text files and update queues."""
        current_time = time.time()
        
        # Only poll at intervals to avoid excessive file I/O
        if current_time - self.last_file_poll_time < self.file_poll_interval:
            return
        
        self.last_file_poll_time = current_time
        
        road_files = {
            ROAD_A: 'lanea.txt',
            ROAD_B: 'laneb.txt',
            ROAD_C: 'lanec.txt',
            ROAD_D: 'laned.txt'
        }
        
        for road_id, file_path in road_files.items():
            try:
                if not os.path.exists(file_path):
                    continue
                
                with open(file_path, 'r') as f:
                    lines = [line.strip() for line in f if line.strip()]
                    
                    # Process new vehicles (those we haven't seen yet)
                    for i in range(self.processed_vehicle_indices[road_id], len(lines)):
                        try:
                            arrival_time = float(lines[i])
                            vehicle = Vehicle(arrival_time)
                            
                            # Distribute across L1, L2, L3 (round-robin)
                            lane_num = (i % 3) + 1
                            lane_key = f'L{lane_num}'
                            
                            if lane_key in self.logic_engine.lanes[road_id]:
                                self.logic_engine.lanes[road_id][lane_key].enqueue(vehicle)
                                
                                # Create visual vehicle
                                self._create_visual_vehicle(road_id, lane_key)
                        
                        except ValueError:
                            continue
                    
                    self.processed_vehicle_indices[road_id] = len(lines)
            
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    def _create_visual_vehicle(self, road_id, lane_key):
        """Create a visual vehicle at the appropriate starting position."""
        lane_num = int(lane_key[1])  # Extract lane number (1, 2, or 3)
        
        # Get starting position based on road and lane
        if road_id == ROAD_A:  # Top (North)
            x = self.junction_center_x - self.road_width//2 + (lane_num - 1) * self.lane_width + self.lane_width//2
            y = 50
        elif road_id == ROAD_B:  # Right (East)
            x = SCREEN_WIDTH - 50
            y = self.junction_center_y - self.road_width//2 + (lane_num - 1) * self.lane_width + self.lane_width//2
        elif road_id == ROAD_C:  # Bottom (South)
            x = self.junction_center_x - self.road_width//2 + (lane_num - 1) * self.lane_width + self.lane_width//2
            y = SCREEN_HEIGHT - 50
        else:  # ROAD_D (Left/West)
            x = 50
            y = self.junction_center_y - self.road_width//2 + (lane_num - 1) * self.lane_width + self.lane_width//2
        
        vehicle = VisualVehicle(
            self.vehicle_counter,
            road_id,
            lane_key,
            (x, y),
            color=VEHICLE_GREEN if lane_key == 'L3' else VEHICLE_BLUE  # Free lanes are green, others blue
        )
        self.visual_vehicles.append(vehicle)
        self.vehicle_counter += 1
    
    def _get_stop_line_position(self, road_id, lane_key):
        """Get the stop line position for a vehicle based on road and lane."""
        lane_num = int(lane_key[1])  # Extract lane number (1, 2, or 3)
        stop_line_offset = 20  # Distance from junction center to stop line
        
        if road_id == ROAD_A:  # North/Top
            x = self.junction_center_x - self.road_width//2 + (lane_num - 1) * self.lane_width + self.lane_width//2
            y = self.junction_center_y - stop_line_offset
            return (x, y)
        elif road_id == ROAD_B:  # East/Right
            x = self.junction_center_x + stop_line_offset
            y = self.junction_center_y - self.road_width//2 + (lane_num - 1) * self.lane_width + self.lane_width//2
            return (x, y)
        elif road_id == ROAD_C:  # South/Bottom
            x = self.junction_center_x - self.road_width//2 + (lane_num - 1) * self.lane_width + self.lane_width//2
            y = self.junction_center_y + stop_line_offset
            return (x, y)
        else:  # ROAD_D (West/Left)
            x = self.junction_center_x - stop_line_offset
            y = self.junction_center_y - self.road_width//2 + (lane_num - 1) * self.lane_width + self.lane_width//2
            return (x, y)
    
    def _is_at_stop_line(self, vehicle, stop_line_pos):
        """Check if vehicle has reached the stop line."""
        x, y = vehicle.position
        sx, sy = stop_line_pos
        distance = ((x - sx)**2 + (y - sy)**2)**0.5
        return distance < 5  # Within 5 pixels of stop line
    
    def _update_free_lane_vehicle(self, vehicle):
        """Update vehicle in free lane (L3) with curved left turn path."""
        road_id = vehicle.road_id
        x, y = vehicle.position
        lane_num = 3
        
        # Get stop line position
        stop_line_pos = self._get_stop_line_position(road_id, vehicle.lane_id)
        sx, sy = stop_line_pos
        
        # Check if vehicle has reached stop line and should start turning
        if not vehicle.turning:
            # Check if approaching stop line
            if road_id == ROAD_A:  # Coming from North
                if y >= sy - 10:  # Near stop line
                    vehicle.turning = True
                    vehicle.turn_progress = 0.0
                    vehicle.start_turn_pos = (x, y)
            elif road_id == ROAD_B:  # Coming from East
                if x <= sx + 10:
                    vehicle.turning = True
                    vehicle.turn_progress = 0.0
                    vehicle.start_turn_pos = (x, y)
            elif road_id == ROAD_C:  # Coming from South
                if y <= sy + 10:
                    vehicle.turning = True
                    vehicle.turn_progress = 0.0
                    vehicle.start_turn_pos = (x, y)
            else:  # ROAD_D (Coming from West)
                if x >= sx - 10:
                    vehicle.turning = True
                    vehicle.turn_progress = 0.0
                    vehicle.start_turn_pos = (x, y)
        
        # If turning, follow curved path
        if vehicle.turning:
            vehicle.turn_progress += 0.02  # Increment turn progress
            
            if vehicle.turn_progress >= 1.0:
                # Turn complete, continue in new direction
                vehicle.turning = False
                # Determine exit direction (left turn from each road)
                if road_id == ROAD_A:  # North -> West
                    vehicle.road_id = ROAD_D
                    x -= vehicle.speed
                elif road_id == ROAD_B:  # East -> North
                    vehicle.road_id = ROAD_A
                    y -= vehicle.speed
                elif road_id == ROAD_C:  # South -> East
                    vehicle.road_id = ROAD_B
                    x += vehicle.speed
                else:  # ROAD_D -> South
                    vehicle.road_id = ROAD_C
                    y += vehicle.speed
            else:
                # Follow curved path using bezier or arc
                # Simple arc approximation
                if road_id == ROAD_A:  # North -> West (left turn)
                    # Arc from (sx, sy) curving left
                    angle = vehicle.turn_progress * 90  # 90 degree turn
                    radius = 40
                    center_x = sx - radius
                    center_y = sy
                    rad_angle = math.radians(angle)
                    x = center_x + radius * math.cos(rad_angle)
                    y = center_y - radius * math.sin(rad_angle)
                elif road_id == ROAD_B:  # East -> North
                    angle = vehicle.turn_progress * 90
                    radius = 40
                    center_x = sx
                    center_y = sy - radius
                    rad_angle = math.radians(angle)
                    x = center_x - radius * math.sin(rad_angle)
                    y = center_y + radius * math.cos(rad_angle)
                elif road_id == ROAD_C:  # South -> East
                    angle = vehicle.turn_progress * 90
                    radius = 40
                    center_x = sx + radius
                    center_y = sy
                    rad_angle = math.radians(angle)
                    x = center_x - radius * math.cos(rad_angle)
                    y = center_y + radius * math.sin(rad_angle)
                else:  # ROAD_D -> South
                    angle = vehicle.turn_progress * 90
                    radius = 40
                    center_x = sx
                    center_y = sy + radius
                    rad_angle = math.radians(angle)
                    x = center_x + radius * math.sin(rad_angle)
                    y = center_y - radius * math.cos(rad_angle)
        else:
            # Move normally toward stop line
            if road_id == ROAD_A:  # Moving South
                y += vehicle.speed
            elif road_id == ROAD_B:  # Moving West
                x -= vehicle.speed
            elif road_id == ROAD_C:  # Moving North
                y -= vehicle.speed
            else:  # ROAD_D (Moving East)
                x += vehicle.speed
        
        vehicle.position = (x, y)
        return False  # Don't remove yet
    
    def update_vehicles(self):
        """Update vehicle positions based on traffic light states, stop lines, and lane types."""
        # Get traffic light states from logic engine
        light_states = self.logic_engine.light_states
        
        vehicles_to_remove = []
        
        for vehicle in self.visual_vehicles:
            road_id = vehicle.road_id
            lane_key = vehicle.lane_id
            x, y = vehicle.position
            
            # Check if this is a free lane (L3) - always allowed to move and turn left
            is_free_lane = lane_key == 'L3'
            
            if is_free_lane:
                # Free lane vehicles turn left immediately with curved path
                if self._update_free_lane_vehicle(vehicle):
                    vehicles_to_remove.append(vehicle)
                continue
            
            # For regular lanes (L1, L2), check stop line and traffic light
            stop_line_pos = self._get_stop_line_position(road_id, lane_key)
            is_green = light_states[road_id] == TrafficLightState.GREEN
            
            # Check if vehicle is at or past stop line
            at_stop_line = self._is_at_stop_line(vehicle, stop_line_pos)
            past_stop_line = False
            
            # Determine if vehicle has passed stop line
            if road_id == ROAD_A:  # Moving South
                past_stop_line = y > stop_line_pos[1]
            elif road_id == ROAD_B:  # Moving West
                past_stop_line = x < stop_line_pos[0]
            elif road_id == ROAD_C:  # Moving North
                past_stop_line = y < stop_line_pos[1]
            else:  # ROAD_D (Moving East)
                past_stop_line = x > stop_line_pos[0]
            
            # Vehicle can move if:
            # 1. Hasn't reached stop line yet, OR
            # 2. Has passed stop line (already in junction), OR
            # 3. Green light and at stop line
            can_move = not at_stop_line or past_stop_line or (is_green and at_stop_line)
            
            if can_move:
                # Move vehicle along its lane center
                lane_num = int(lane_key[1])
                
                # Calculate lane center position
                if road_id == ROAD_A:  # Moving South (down)
                    target_x = self.junction_center_x - self.road_width//2 + (lane_num - 1) * self.lane_width + self.lane_width//2
                    # Move toward lane center if not aligned
                    if abs(x - target_x) > 1:
                        x += (target_x - x) * 0.1  # Smooth alignment
                    y += vehicle.speed
                    if y > SCREEN_HEIGHT:
                        vehicles_to_remove.append(vehicle)
                elif road_id == ROAD_B:  # Moving West (left)
                    target_y = self.junction_center_y - self.road_width//2 + (lane_num - 1) * self.lane_width + self.lane_width//2
                    if abs(y - target_y) > 1:
                        y += (target_y - y) * 0.1
                    x -= vehicle.speed
                    if x < 0:
                        vehicles_to_remove.append(vehicle)
                elif road_id == ROAD_C:  # Moving North (up)
                    target_x = self.junction_center_x - self.road_width//2 + (lane_num - 1) * self.lane_width + self.lane_width//2
                    if abs(x - target_x) > 1:
                        x += (target_x - x) * 0.1
                    y -= vehicle.speed
                    if y < 0:
                        vehicles_to_remove.append(vehicle)
                else:  # ROAD_D (Moving East/right)
                    target_y = self.junction_center_y - self.road_width//2 + (lane_num - 1) * self.lane_width + self.lane_width//2
                    if abs(y - target_y) > 1:
                        y += (target_y - y) * 0.1
                    x += vehicle.speed
                    if x > SCREEN_WIDTH:
                        vehicles_to_remove.append(vehicle)
                
                vehicle.position = (x, y)
        
        # Remove vehicles that left the screen
        for vehicle in vehicles_to_remove:
            # Dequeue from logic engine if still in queue
            road_id = vehicle.road_id
            lane_key = vehicle.lane_id
            if lane_key in self.logic_engine.lanes[road_id]:
                lane = self.logic_engine.lanes[road_id][lane_key]
                if not lane.is_empty():
                    lane.dequeue()
            self.visual_vehicles.remove(vehicle)
    
    def draw_junction(self):
        """Draw the 4-way junction with continuous cross-shaped roads."""
        # Draw background (dark green grass)
        self.screen.fill(DARK_GREEN)
        
        # Draw roads as a continuous cross shape (dark gray)
        # Vertical road (North-South) - continuous through center
        pygame.draw.rect(self.screen, ROAD_GRAY, (
            self.junction_center_x - self.road_width//2,
            0,
            self.road_width,
            SCREEN_HEIGHT
        ))
        
        # Horizontal road (East-West) - continuous through center
        pygame.draw.rect(self.screen, ROAD_GRAY, (
            0,
            self.junction_center_y - self.road_width//2,
            SCREEN_WIDTH,
            self.road_width
        ))
        
        # Draw direction separators (solid yellow lines in the middle)
        self._draw_direction_separators()
        
        # Draw lane dividers (dashed white lines)
        self._draw_lane_dividers()
        
        # Draw road labels
        self._draw_road_labels()
    
    def _draw_direction_separators(self):
        """Draw solid yellow lines to separate incoming and outgoing traffic directions."""
        # Vertical road (North-South): horizontal yellow line in the middle
        center_y = self.junction_center_y
        pygame.draw.line(self.screen, YELLOW, 
                        (self.junction_center_x - self.road_width//2, center_y),
                        (self.junction_center_x + self.road_width//2, center_y), 3)
        
        # Horizontal road (East-West): vertical yellow line in the middle
        center_x = self.junction_center_x
        pygame.draw.line(self.screen, YELLOW,
                        (center_x, self.junction_center_y - self.road_width//2),
                        (center_x, self.junction_center_y + self.road_width//2), 3)
    
    def _draw_lane_dividers(self):
        """Draw dashed white lines to separate the three lanes on each road."""
        dash_length = 10
        gap_length = 5
        
        # Vertical dividers for vertical road (North-South)
        # Two dividers: between L1-L2 and L2-L3
        for i in range(1, 3):
            x_offset = self.junction_center_x - self.road_width//2 + i * self.lane_width
            y = 0
            while y < SCREEN_HEIGHT:
                # Draw dash
                end_y = min(y + dash_length, SCREEN_HEIGHT)
                pygame.draw.line(self.screen, WHITE, (x_offset, y), (x_offset, end_y), 2)
                y += dash_length + gap_length
        
        # Horizontal dividers for horizontal road (East-West)
        # Two dividers: between L1-L2 and L2-L3
        for i in range(1, 3):
            y_offset = self.junction_center_y - self.road_width//2 + i * self.lane_width
            x = 0
            while x < SCREEN_WIDTH:
                # Draw dash
                end_x = min(x + dash_length, SCREEN_WIDTH)
                pygame.draw.line(self.screen, WHITE, (x, y_offset), (end_x, y_offset), 2)
                x += dash_length + gap_length
    
    def _draw_road_labels(self):
        """Draw road labels (A, B, C, D)."""
        label_offset = 30
        
        # Road A (Top) - white text for visibility on dark green
        text = self.font.render("Road A", True, WHITE)
        self.screen.blit(text, (self.junction_center_x - 40, label_offset))
        
        # Road B (Right)
        text = self.font.render("Road B", True, WHITE)
        self.screen.blit(text, (SCREEN_WIDTH - 100, self.junction_center_y - 10))
        
        # Road C (Bottom)
        text = self.font.render("Road C", True, WHITE)
        self.screen.blit(text, (self.junction_center_x - 40, SCREEN_HEIGHT - label_offset - 20))
        
        # Road D (Left)
        text = self.font.render("Road D", True, WHITE)
        self.screen.blit(text, (label_offset, self.junction_center_y - 10))
    
    def draw_traffic_lights(self):
        """Draw traffic light status for each road at inner corners of junction near stop lines."""
        light_size = 20
        stop_line_offset = 20  # Distance from junction center to stop line (where lights are placed)
        
        center_x = self.junction_center_x
        center_y = self.junction_center_y
        road_half = self.road_width // 2
        lane_width = self.lane_width
        
        # Calculate stop line positions at inner corners of junction
        # Each road has a pair of lights near the stop line (positioned between lanes)
        # Lights are placed at the inner corners where roads meet the junction center
        light_positions = {
            # Road A (North/Top): approaching from top, lights at bottom edge of junction
            # Positioned between lanes, near the stop line
            ROAD_A: [
                (center_x - road_half + lane_width, center_y - stop_line_offset),  # Left light (between L1-L2)
                (center_x - road_half + 2 * lane_width, center_y - stop_line_offset)  # Right light (between L2-L3)
            ],
            # Road B (East/Right): approaching from right, lights at left edge of junction
            ROAD_B: [
                (center_x + stop_line_offset, center_y - road_half + lane_width),  # Top light (between L1-L2)
                (center_x + stop_line_offset, center_y - road_half + 2 * lane_width)  # Bottom light (between L2-L3)
            ],
            # Road C (South/Bottom): approaching from bottom, lights at top edge of junction
            ROAD_C: [
                (center_x - road_half + lane_width, center_y + stop_line_offset),  # Left light (between L1-L2)
                (center_x - road_half + 2 * lane_width, center_y + stop_line_offset)  # Right light (between L2-L3)
            ],
            # Road D (West/Left): approaching from left, lights at right edge of junction
            ROAD_D: [
                (center_x - stop_line_offset, center_y - road_half + lane_width),  # Top light (between L1-L2)
                (center_x - stop_line_offset, center_y - road_half + 2 * lane_width)  # Bottom light (between L2-L3)
            ]
        }
        
        # Draw lights for each road
        for road_id, positions in light_positions.items():
            # Get traffic light state from logic engine
            state = self.logic_engine.light_states[road_id]
            
            # Determine color based on state (State 1: Red, State 2: Green)
            # TrafficLightState.RED = State 1, TrafficLightState.GREEN = State 2
            color = GREEN if state == TrafficLightState.GREEN else RED
            
            # Draw light pair for each road (one light for each side of the road)
            for i, (x, y) in enumerate(positions):
                # Draw light circle with border
                pygame.draw.circle(self.screen, color, (int(x), int(y)), light_size)
                pygame.draw.circle(self.screen, BLACK, (int(x), int(y)), light_size, 2)
                
                # Draw a small white border for better visibility on dark background
                pygame.draw.circle(self.screen, WHITE, (int(x), int(y)), light_size + 1, 1)
    
    def draw_lane_info(self):
        """Draw lane information (vehicle counts, free lane indicators)."""
        info_y = 10
        info_x = SCREEN_WIDTH - 200
        
        # Draw header with white text for visibility on dark green
        header = self.small_font.render("Lane Status", True, WHITE)
        self.screen.blit(header, (info_x, info_y))
        info_y += 25
        
        for road_id in [ROAD_A, ROAD_B, ROAD_C, ROAD_D]:
            road_text = self.small_font.render(f"Road {road_id}:", True, WHITE)
            self.screen.blit(road_text, (info_x, info_y))
            info_y += 20
            
            for lane_key in ['L1', 'L2', 'L3']:
                if lane_key in self.logic_engine.lanes[road_id]:
                    lane = self.logic_engine.lanes[road_id][lane_key]
                    count = len(lane)
                    is_free = lane_key == 'L3'
                    free_text = " [FREE]" if is_free else ""
                    lane_text = self.small_font.render(
                        f"  {lane_key}: {count} vehicles{free_text}", True, WHITE
                    )
                    self.screen.blit(lane_text, (info_x, info_y))
                    info_y += 18
            
            info_y += 5
    
    def draw_vehicles(self):
        """Draw all visual vehicles."""
        for vehicle in self.visual_vehicles:
            vehicle.draw(self.screen)
    
    def run(self):
        """Main simulation loop."""
        last_cycle_time = time.time()
        cycle_interval = 5.0  # Run logic engine cycle every 5 seconds
        
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
            
            # Poll lane files
            self.poll_lane_files()
            
            # Run logic engine cycle periodically
            current_time = time.time()
            if current_time - last_cycle_time >= cycle_interval:
                road, vehicles, duration, was_priority = self.logic_engine.run_cycle()
                if was_priority:
                    print(f"High Priority: Road {road} served {vehicles} vehicles")
                last_cycle_time = current_time
            
            # Update vehicle positions
            self.update_vehicles()
            
            # Draw everything
            self.draw_junction()
            self.draw_traffic_lights()
            self.draw_lane_info()
            self.draw_vehicles()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        pygame.quit()


if __name__ == "__main__":
    simulator = TrafficSimulator()
    simulator.run()

