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
                    # Random Spawn Request
                    if random.random() < 0.2: # Control spawn rate
                        r_id = random.choice(['A', 'B', 'C', 'D'])
                        # Higher chance for AL2 to test priority
                        if random.random() < 0.4:
                            l_id = 'L2'
                        else:
                            l_id = random.choice(['L1', 'L2', 'L3'])
                        
                        msg = f"{r_id}:{l_id}"
                        try:
                            s.sendall(msg.encode())
                            # print(f"Sent: {msg}")
                        except Exception as e:
                            print(f"Error sending: {e}")
                            break
                    
                    time.sleep(0.1) # Simulate real-time delay
                    
        except ConnectionRefusedError:
            print("Simulator not running. Retrying in 2s...")
            time.sleep(2)
        except Exception as e:
            print(f"Connection Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
