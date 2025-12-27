import pygame
import math
from utils import *
from simulation import STATE_1, STATE_2

# Colors
# Colors - Restyled
GRASS_COLOR = (45, 60, 45) # Dark Green
ROAD_COLOR = (60, 60, 70) # Dark Grey
MARKING_WHITE = (240, 240, 240)

class Visualizer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("Verdana", 12, bold=True)

    def draw_environment(self):
        self.screen.fill(GRASS_COLOR)
        
        # Roads
        pygame.draw.rect(self.screen, ROAD_COLOR, (CX - INTERSECTION_SIZE//2, 0, INTERSECTION_SIZE, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, ROAD_COLOR, (0, CY - INTERSECTION_SIZE//2, SCREEN_WIDTH, INTERSECTION_SIZE))
        # Center Intersection (same color as road to blend)
        pygame.draw.rect(self.screen, ROAD_COLOR, (CX - INTERSECTION_SIZE//2, CY - INTERSECTION_SIZE//2, INTERSECTION_SIZE, INTERSECTION_SIZE))

        # Dotted Intersection Outline - Removed as per user request
        # self._draw_intersection_dots()

        # Crosswalks
        self._draw_crosswalks()

        # Lane Markings
        self._draw_markings()

    def _draw_intersection_dots(self):
        # Dotted square around the intersection area to delineate it
        half = INTERSECTION_SIZE // 2
        # Use big white dots
        
        # Top Edge
        self._dotted_line((CX - half, CY - half), (CX + half, CY - half))
        # Bot Edge
        self._dotted_line((CX - half, CY + half), (CX + half, CY + half))
        # Left Edge
        self._dotted_line((CX - half, CY - half), (CX - half, CY + half))
        # Right Edge
        self._dotted_line((CX + half, CY - half), (CX + half, CY + half))
        
    def _dotted_line(self, start, end):
        # Big square dots
        x1, y1 = start
        x2, y2 = end
        dist = math.hypot(x2-x1, y2-y1)
        steps = int(dist // 20) # 20px gaps
        
        for i in range(steps + 1):
             t = i / steps if steps > 0 else 0
             x = x1 + (x2-x1)*t
             y = y1 + (y2-y1)*t
             pygame.draw.rect(self.screen, MARKING_WHITE, (x-4, y-4, 8, 8))

    def _draw_crosswalks(self):
        # Draw zebra stripes at the 4 entrances
        half = INTERSECTION_SIZE // 2
        
        # Top Crosswalk
        y = CY - half - 10
        self._zebra_h(CX - half, CX + half, y)
        
        # Bottom Crosswalk
        y = CY + half + 2
        self._zebra_h(CX - half, CX + half, y)

        # Left Crosswalk
        x = CX - half - 10
        self._zebra_v(CY - half, CY + half, x)
        
        # Right Crosswalk
        x = CX + half + 2
        self._zebra_v(CY - half, CY + half, x)

    def _zebra_h(self, x1, x2, y):
        for x in range(int(x1), int(x2), 15):
             pygame.draw.rect(self.screen, MARKING_WHITE, (x, y, 8, 8))

    def _zebra_v(self, y1, y2, x):
         for y in range(int(y1), int(y2), 15):
             pygame.draw.rect(self.screen, MARKING_WHITE, (x, y, 8, 8))

    def _draw_markings(self):
        # Lane Markings (2 STRIPPED LINES PER ROAD -> 3 LANES)
        # Offsets -27, 27 to divide 160px road into 3 lanes (~53px each)
        
        # Vertical Roads (A, C)
        for x_off in [-27, 27]:
            self._dashed((CX - x_off, 0), (CX - x_off, CY - INTERSECTION_SIZE//2 - 12))
            self._dashed((CX - x_off, CY + INTERSECTION_SIZE//2 + 12), (CX - x_off, SCREEN_HEIGHT))

        # Horizontal Roads (B, D)
        for y_off in [-27, 27]:
            self._dashed((0, CY - y_off), (CX - INTERSECTION_SIZE//2 - 12, CY - y_off))
            self._dashed((CX + INTERSECTION_SIZE//2 + 12, CY - y_off), (SCREEN_WIDTH, CY - y_off))
    
    def _dashed(self, start, end):
        # Custom Dash
        x1, y1 = start
        x2, y2 = end
        dist = math.hypot(x2-x1, y2-y1)
        steps = int(dist // 20) # 20px gap
        
        for i in range(steps):
             t = i / steps
             t2 = (i + 0.5) / steps
             
             sx = x1 + (x2-x1)*t
             sy = y1 + (y2-y1)*t
             ex = x1 + (x2-x1)*t2
             ey = y1 + (y2-y1)*t2
             
             pygame.draw.line(self.screen, MARKING_WHITE, (sx, sy), (ex, ey), 2)
             
    def draw_traffic_lights(self, intersection):
        # Draw one light per road, positioned between L1 and L2
        for r_id, road in intersection.roads.items():
            # Get midpoint between L1 and L2 stop positions
            p1 = road.L1.stop_pos
            p2 = road.L2.stop_pos
            pos = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
            
            state = road.main_light.state
            
            # Draw Box
            rect = pygame.Rect(0, 0, 24, 24)
            rect.center = pos
            pygame.draw.rect(self.screen, (20, 20, 20), rect, border_radius=4)
            
            # Draw Light Circle
            color = (0, 255, 0) if state == STATE_2 else (255, 0, 0)
            pygame.draw.circle(self.screen, color, pos, 10)
            
            # Glow effect
            s = pygame.Surface((44, 44), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, 60), (22, 22), 18)
            self.screen.blit(s, s.get_rect(center=pos))

    def draw_vehicles(self, vehicles):
        for v in vehicles:
            self._draw_vehicle(v)
            
    def draw_queues(self, intersection):
        # Draw queued vehicles stacked behind stop line
        for r in intersection.roads.values():
            for lane in [r.L1, r.L2, r.L3]:
                for v in lane.vehicles:
                    self._draw_static_car(v, lane)

    def _draw_static_car(self, v, lane):
        color = v.color
        
        rect = pygame.Rect(0,0, 24, 14)
        rect.center = (v.x, v.y)
        if lane.road_id in ['A', 'C']:
            rect = pygame.Rect(0,0, 14, 24)
            rect.center = (v.x, v.y)
            
        pygame.draw.rect(self.screen, color, rect, border_radius=4)


    def _draw_vehicle(self, v):
        # Moving vehicle
        color = getattr(v, 'color', (255, 255, 0))
        s = pygame.Surface((24, 14), pygame.SRCALPHA)
        pygame.draw.rect(s, color, (0,0,24,14), border_radius=4)
        rot = pygame.transform.rotate(s, -math.degrees(v.angle))
        r = rot.get_rect(center=(v.x, v.y))
        self.screen.blit(rot, r)
    
    def draw_ui(self, intersection):
        # Debug UI removed as per user request
        pass


