import socket
import time
import random
from utils import *

def main():
    print(f"Traffic Generator connect to {HOST}:{PORT}...")
    
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                print("Connected to Simulator!")
                
                while True:
                    # weighted choice: AL2 is much more likely
                    # Combinations: (A/B/C/D) x (L1/L2/L3) = 12 total
                    # Let's give AL2 a 40% chance, others split the rest
                    roads = ['A', 'B', 'C', 'D']
                    lanes = ['L1', 'L2', 'L3']
                    
                    if random.random() < 0.7:
                        r, l = 'A', 'L2'
                    else:
                        r = random.choice(roads)
                        l = random.choice(lanes)
                    
                    msg = f"{r}:{l}"
                    try:
                        s.sendall(msg.encode())
                        print(f"[{time.strftime('%H:%M:%S')}] Spawned vehicle: {r}:{l}")
                    except Exception as e:
                        print(f"Error sending: {e}")
                        break
                    
                    time.sleep(0.8) # Faster generation (approx. 75 vehicles/min)
                    
        except ConnectionRefusedError:
            print("Simulator not running. Retrying in 2s...")
            time.sleep(2)
        except Exception as e:
            print(f"Connection Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
