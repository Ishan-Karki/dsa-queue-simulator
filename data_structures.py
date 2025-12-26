import time
from constants import ROAD_GRAY

class Vehicle:
    def __init__(self, lane_id, x, y, dx, dy):
        self.lane_id = lane_id
        self.x = x
        self.y = y
        self.dx = dx # Horizontal speed
        self.dy = dy # Vertical speed
        self.speed = 2
        self.crossed = False

    def move(self, can_move):
        if can_move:
            self.x += self.dx * self.speed
            self.y += self.dy * self.speed

    def draw(self, screen):
        import pygame
        # Draw a small rectangle for the car
        pygame.draw.rect(screen, (100, 149, 237), (self.x, self.y, 20, 20))