import pygame
import sys
import threading
import socket
import select
from utils import *
from visuals import Visualizer
from simulation import Intersection, Vehicle

# Thread-safe queue for incoming vehicle requests if needed, 
# or just modify simulation directly with locks.
# Since python is GIL, simple appends are atomic-ish, but let's be safe.
lock = threading.Lock()

def socket_server(sim):
    """Background thread to handle incoming traffic data"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Simulator listening on {HOST}:{PORT}")
    
    server.setblocking(False)
    
    inputs = [server]
    
    while True:
        readable, _, _ = select.select(inputs, [], [], 0.1)
        
        for s in readable:
            if s is server:
                conn, addr = s.accept()
                conn.setblocking(False)
                inputs.append(conn)
                print(f"Client connected: {addr}")
            else:
                try:
                    data = s.recv(1024)
                    if data:
                        text = data.decode()
                        # Handle multiple packets "A:L2B:L1" if stuck together?
                        # Assuming generator sends one by one with delay, but tcp stream.
                        # Naive parsing:
                        if ':' in text:
                            parts = text.split(':') # Assume A:L2
                            # If multiple messages come: "A:L2A:L1" -> need better buffer handling
                            # For assignment, let's assume simple chunks.
                            # Better: A:L2|B:L1|...
                            
                            # Let's try to parse all occurrences
                            # Just taking the first valid pair for now or splitting by custom delimiter?
                            # Generator sends "ID:LANE".
                            # Let's handle just the raw string for now.
                            
                            # Sanitize
                            clean = text.strip()
                            # It might be "A:L2"
                            if len(clean) >= 4:
                                r_id = clean[0]
                                l_id = clean[2:4]
                                
                                if r_id in ['A', 'B', 'C', 'D'] and l_id in ['L1', 'L2', 'L3']:
                                    with lock:
                                        sim.add_vehicle(r_id, l_id)
                                        
                    else:
                        inputs.remove(s)
                        s.close()
                except Exception as e:
                    inputs.remove(s)
                    s.close()

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Smart 3-Lane Traffic Simulator (Server)")
    clock = pygame.time.Clock()
    
    viz = Visualizer(screen)
    sim = Intersection()
    
    # Start Server Thread
    server_thread = threading.Thread(target=socket_server, args=(sim,), daemon=True)
    server_thread.start()
    
    running = True
    
    while running:
        clock.tick(FPS)
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            
        # Update Simulation
        with lock:
            sim.update()
            
            # Move Vehicles
            active_v = []
            for v in sim.moving_vehicles:
                v.update()
                if v.state != 'EXITED':
                    active_v.append(v)
            sim.moving_vehicles = active_v
        
        # Draw
        viz.draw_environment()
        
        # Draw Queues & Vehicles
        # We need to access sim safely? read is usually fine.
        viz.draw_queues(sim) 
        viz.draw_vehicles(sim.moving_vehicles)
        viz.draw_traffic_lights(sim)
        viz.draw_ui(sim)
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
