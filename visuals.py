import pygame
import math
from utils import *

# Colors
GRASS_COLOR = (34, 139, 34)
ROAD_COLOR = (50, 50, 50)
MARKING_WHITE = (220, 220, 220)
MARKING_YELLOW = (220, 200, 0)

class Visualizer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("Verdana", 12, bold=True)

    def draw_environment(self):
        self.screen.fill(GRASS_COLOR)
        
        # Roads
        pygame.draw.rect(self.screen, ROAD_COLOR, (CX - INTERSECTION_SIZE//2, 0, INTERSECTION_SIZE, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, ROAD_COLOR, (0, CY - INTERSECTION_SIZE//2, SCREEN_WIDTH, INTERSECTION_SIZE))
        pygame.draw.rect(self.screen, (60, 60, 60), (CX - INTERSECTION_SIZE//2, CY - INTERSECTION_SIZE//2, INTERSECTION_SIZE, INTERSECTION_SIZE))

        # Highlight Priority Lane (AL2)
        self._highlight_priority_lane()

        # Lane Markings
        self._draw_markings()
        
        # Visual Helpers
        self._draw_road_labels()
        self._draw_lane_arrows()

    def _draw_markings(self):
        # Yellow Center Lines
        pygame.draw.line(self.screen, MARKING_YELLOW, (CX, 0), (CX, CY - INTERSECTION_SIZE//2), 3) # Top
        pygame.draw.line(self.screen, MARKING_YELLOW, (CX, CY + INTERSECTION_SIZE//2), (CX, SCREEN_HEIGHT), 3) # Bot
        pygame.draw.line(self.screen, MARKING_YELLOW, (0, CY), (CX - INTERSECTION_SIZE//2, CY), 3) # Left
        pygame.draw.line(self.screen, MARKING_YELLOW, (CX + INTERSECTION_SIZE//2, CY), (SCREEN_WIDTH, CY), 3) # Right
        
        # Dashed White Lines for Lanes
        # A (Top): Left side has 3 lanes. x = CX - 40, CX - 80.
        # Right side has 3 lanes. x = CX + 40, CX + 80.
        for off in [40, 80]:
            # Vertical
            self._dashed((CX-off, 0), (CX-off, CY-INTERSECTION_SIZE//2))
            self._dashed((CX+off, 0), (CX+off, CY-INTERSECTION_SIZE//2))
            self._dashed((CX-off, CY+INTERSECTION_SIZE//2), (CX-off, SCREEN_HEIGHT))
            self._dashed((CX+off, CY+INTERSECTION_SIZE//2), (CX+off, SCREEN_HEIGHT))
            
            # Horizontal
            self._dashed((0, CY-off), (CX-INTERSECTION_SIZE//2, CY-off))
            self._dashed((CX+INTERSECTION_SIZE//2, CY-off), (SCREEN_WIDTH, CY-off))
            self._dashed((0, CY+off), (CX-INTERSECTION_SIZE//2, CY+off))
            self._dashed((CX+INTERSECTION_SIZE//2, CY+off), (SCREEN_WIDTH, CY+off))

    def _dashed(self, start, end):
        pygame.draw.line(self.screen, MARKING_WHITE, start, end, 1)

    def draw_traffic_lights(self, intersection):
        # Draw lights at stop pos of each lane
        for r_id, road in intersection.roads.items():
            for lane in [road.L1, road.L2, road.L3]:
                pos = lane.stop_pos
                state = lane.light.state
                
                # Draw Box
                rect = pygame.Rect(0, 0, 20, 20)
                rect.center = pos
                pygame.draw.rect(self.screen, (0, 0, 0), rect)
                
                # Draw Light Circle
                color = (0, 255, 0) if state == 'GREEN' else (255, 0, 0)
                pygame.draw.circle(self.screen, color, pos, 8)
                
                # Glow effect
                s = pygame.Surface((40, 40), pygame.SRCALPHA)
                pygame.draw.circle(s, (*color, 50), (20, 20), 15)
                self.screen.blit(s, s.get_rect(center=pos))

    def draw_vehicles(self, vehicles):
        for v in vehicles:
            self._draw_vehicle(v)
            
    def draw_queues(self, intersection):
        # Draw queued vehicles stacked behind stop line
        for r in intersection.roads.values():
            for lane in [r.L1, r.L2, r.L3]:
                for i, v in enumerate(lane.vehicles):
                    # Stack them visually backwards from stop_pos
                    # Needs Direction vector
                    # A (Top): Up direction (0, -1)
                    # B (Right): Right direction (1, 0)? No, Inbound is Left. (-1, 0)??
                    # Queue grows AWAY from intersection.
                    # A (Top): Queue grows Up (y decreases).
                    # B (Right): Queue grows Right (x increases).
                    # C (Bot): Queue grows Down (y increases).
                    # D (Left): Queue grows Left (x decreases).
                    
                    sx, sy = lane.stop_pos
                    gap = 25
                    
                    if r.id == 'A': y = sy - (i+1)*gap; x = sx
                    elif r.id == 'C': y = sy + (i+1)*gap; x = sx
                    elif r.id == 'B': x = sx + (i+1)*gap; y = sy # B Inbound comes from Right side, so Queue is on Right
                    elif r.id == 'D': x = sx - (i+1)*gap; y = sy
                    
                    self._draw_static_car(x, y, r.id, lane.name)

    def _draw_static_car(self, x, y, rid, lname):
        color = (255, 50, 50)
        if lname == 'L2': color = (50, 100, 255)
        
        rect = pygame.Rect(0,0, 24, 14)
        rect.center = (x, y)
        if rid in ['A', 'C']:
            rect = pygame.Rect(0,0, 14, 24)
            rect.center = (x, y)
            
        pygame.draw.rect(self.screen, color, rect, border_radius=4)


    def _draw_vehicle(self, v):
        # Moving vehicle
        color = (255, 255, 0)
        s = pygame.Surface((24, 14), pygame.SRCALPHA)
        pygame.draw.rect(s, color, (0,0,24,14), border_radius=4)
        rot = pygame.transform.rotate(s, -math.degrees(v.angle))
        r = rot.get_rect(center=(v.x, v.y))
        self.screen.blit(rot, r)
    
    def draw_ui(self, intersection):
        txt = f"Priority Mode: {intersection.priority_mode}"
        self.screen.blit(self.font.render(txt, True, (255, 255, 255)), (10, 10))
        
        y = 30
        for rid, r in intersection.roads.items():
            t = f"Road {rid} L2 Queue: {len(r.L2.vehicles)}"
            c = (255, 100, 100) if len(r.L2.vehicles) > 10 else (255, 255, 255)
            self.screen.blit(self.font.render(t, True, c), (10, y))
            y += 20

    def _highlight_priority_lane(self):
        # Road A (Top), Lane 2 (Middle)
        # Vertical strip from Top to Intersection
        # X range: CX - 80 to CX - 40
        # Y range: 0 to CY - INTERSECTION_SIZE//2
        
        surface = pygame.Surface((40, CY - INTERSECTION_SIZE//2), pygame.SRCALPHA)
        surface.fill((255, 215, 0, 50)) # Gold tint, transparent
        self.screen.blit(surface, (CX - 80, 0))
        
    def _draw_road_labels(self):
        labels = [
            ('A', (CX, 20)),
            ('B', (SCREEN_WIDTH - 20, CY)),
            ('C', (CX, SCREEN_HEIGHT - 20)),
            ('D', (20, CY))
        ]
        
        # Larger font for Labels
        font = pygame.font.SysFont("Verdana", 24, bold=True)
        
        for text, (x, y) in labels:
            surf = font.render(text, True, (255, 255, 255))
            rect = surf.get_rect(center=(x, y))
            self.screen.blit(surf, rect)

    def _draw_lane_arrows(self):
        # Draw arrows for L3 (Free Left)
        # Position slightly upstream from stop line
        offset = 60 
        
        # A-L3 (Top, Leftmost incoming) -> Turn Left
        self._draw_arrow((CX - 100, CY - INTERSECTION_SIZE//2 - offset), "DOWN_LEFT")
        
        # B-L3 (Right, Topmost incoming) -> Turn Left
        self._draw_arrow((CX + INTERSECTION_SIZE//2 + offset, CY - 100), "LEFT_DOWN")
        
        # C-L3 (Bot, Rightmost incoming) -> Turn Left
        self._draw_arrow((CX + 100, CY + INTERSECTION_SIZE//2 + offset), "UP_RIGHT")
        
        # D-L3 (Left, Botmost incoming) -> Turn Left
        self._draw_arrow((CX - INTERSECTION_SIZE//2 - offset, CY + 100), "RIGHT_UP")

    def _draw_arrow(self, pos, direction):
        x, y = pos
        # pygame.draw.circle(self.screen, (255, 255, 255), (int(x), int(y)), 2)
        
        c = (200, 200, 200)
        w = 3
        sz = 15
        
        if direction == "DOWN_LEFT":
            pygame.draw.line(self.screen, c, (x, y-sz), (x, y), w) # Straight
            pygame.draw.line(self.screen, c, (x, y), (x-sz, y+sz//2), w) # Turn
            # Arrowhead
            pygame.draw.line(self.screen, c, (x-sz, y+sz//2), (x-sz+5, y+sz//2-5), w)
            pygame.draw.line(self.screen, c, (x-sz, y+sz//2), (x-sz+5, y+sz//2+5), w)
            
        elif direction == "LEFT_DOWN":
            pygame.draw.line(self.screen, c, (x+sz, y), (x, y), w)
            pygame.draw.line(self.screen, c, (x, y), (x-sz//2, y+sz), w)
            # Arrowhead
            pygame.draw.line(self.screen, c, (x-sz//2, y+sz), (x-sz//2+5, y+sz-5), w)
            pygame.draw.line(self.screen, c, (x-sz//2, y+sz), (x-sz//2-5, y+sz-5), w)

        elif direction == "UP_RIGHT":
            pygame.draw.line(self.screen, c, (x, y+sz), (x, y), w)
            pygame.draw.line(self.screen, c, (x, y), (x+sz, y-sz//2), w)
            # Arrowhead
            pygame.draw.line(self.screen, c, (x+sz, y-sz//2), (x+sz-5, y-sz//2-5), w)
            pygame.draw.line(self.screen, c, (x+sz, y-sz//2), (x+sz-5, y-sz//2+5), w)

        elif direction == "RIGHT_UP":
            pygame.draw.line(self.screen, c, (x-sz, y), (x, y), w)
            pygame.draw.line(self.screen, c, (x, y), (x+sz//2, y-sz), w)
            # Arrowhead
            pygame.draw.line(self.screen, c, (x+sz//2, y-sz), (x+sz//2-5, y-sz+5), w)
            pygame.draw.line(self.screen, c, (x+sz//2, y-sz), (x+sz//2+5, y-sz+5), w)
