import time
import random

def generate():
    print("Generator Started. Writing to lane files...")
    roads = ['a', 'b', 'c', 'd']
    
    while True:
        # Pick a random road and lane
        r = random.choice(roads)
        # Lane 1, 2, or 3
        l = random.randint(1, 3)
        
        # Write to file
        filename = f"lane{r}.txt"
        try:
            with open(filename, 'a') as f:
                f.write(f"L{l}\n")
            print(f"Spawned Vehicle at {r.upper()} L{l}")
        except:
            pass
            
        # Random burst logic for Road A (to test Priority)
        if random.random() < 0.3: # 30% chance to spam Road A
             with open("lanea.txt", 'a') as f:
                f.write("L2\n")
             print("Spawned Priority Vehicle at A L2")

        time.sleep(random.uniform(0.5, 1.5))

if __name__ == "__main__":
    generate()