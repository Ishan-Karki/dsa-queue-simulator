# Traffic Queue Simulator

**Name:** Ishan Karki  
**Class:** CS-I  
**Roll no:** 32  
**Assignment:** I  
**Submitted to:** Rupak Ghimire  
**Course:** Data Structure and Algorithms (COMP202)

---

## Introduction
A real-time traffic intersection simulation built with Python and Pygame. This project demonstrates the application of Data Structures and Algorithms (DSA), specifically **Queues** and **Priority Logic**, to efficiently manage traffic flow. The system simulates a 4-way intersection using a client-server architecture where a generator sends traffic data to a simulator.

## Demo Output
- The simulation visualizes cars moving through a 4-way intersection.
- Traffic lights update dynamically based on queue length.
- Priority mode activates when high congestion is detected in specific lanes.

## System Architecture
The project follows a **Client-Server** model:
- **Simulator (`simulator.py` - Server):** Renders the visual environment using Pygame, manages traffic lights state, assigns paths (Bezier curves), and handles vehicle physics. It listens on TCP port 5000.
- **Traffic Generator (`trafficgenerator.py` - Client):** Generates vehicle spawn data based on stochastic patterns and sends it to the simulator via TCP sockets. It manages the logical generation of traffic flow.

## Features
- **Queue-Based Traffic Management:** Vehicles are processed using FIFO (First-In-First-Out) queues.
- **Dynamic Priority System:** Automatically detects congestion (e.g., >10 vehicles in Lane AL2) and overrides normal traffic signals to clear the backlog.
- **Realistic Physics:** Smooth acceleration, deceleration, and turning using Bezier curves.
- **Visuals:** Dark theme with neon accents, dynamic traffic lights, and smooth animations.
- **Networking:** Robust TCP/IP communication separating logic (traffic generation) and presentation (simulation).

## Data Structures Used
- **Queue (FIFO):** Used for managing vehicles in standard lanes waiting for a green light.
- **Priority Queue Logic:** Used for the specific lane monitoring (e.g. 'AL2'). When the vehicle count exceeds a threshold, the system switches context to prioritize this queue.
- **Lists:** Used for storing active vehicle objects, coordinating road segments, and managing simulation entities.

## Installations and Prerequisites
### Requirements
- Python 3.x
- Pygame

### Installation
1. Install Python 3.x from [python.org](https://www.python.org/).
2. Install the necessary library:
   ```bash
   pip install pygame
   ```

## Configuration
- **Port:** Default is `5000`. Can be changed in `simulator.py` and `trafficgenerator.py`.
- **Host:** Default is `localhost`.
- **Thresholds:** Priority triggers can be adjusted in the code (default > 10 vehicles to start priority, < 5 to stop).

## Trouble Shooting
- **Connection Refused:** Ensure `simulator.py` is running *before* `trafficgenerator.py`.
- **Pygame Errors:** Verify that Pygame is installed correctly using `pip list`.
- **Firewall Issues:** Allow Python to access local network ports if prompted/blocked.

## Logic and Algorithms
1.  **Traffic Generation:** The generator randomly selects a lane and vehicle type based on predefined weights and sends this data to the simulator.
2.  **Traffic Control Algorithm:**
    -   **Round Robin (Normal Mode):** Cycles through roads A, B, C, D in order.
    -   **Priority Override:** If `AL2` queue length > 10, the system strictly serves road A (AL2) until queue length < 5, then resumes the Round Robin cycle.
3.  **Green Time Calculation:** Green light duration is dynamic, calculated based on the number of waiting vehicles ($\text{duration} = \text{vehicle\_count} \times \text{time\_per\_car}$).
4.  **Pathing:** Uses quadratic Bezier curves for smooth left and right turns to ensure realistic vehicle movement.

<<<<<<< HEAD
## References
- **Pygame Documentation:** [https://www.pygame.org/docs/](https://www.pygame.org/docs/)
- **Python Socket Programming:** [https://docs.python.org/3/library/socket.html](https://docs.python.org/3/library/socket.html)
- **Bezier Curves:** [Wikipedia](https://en.wikipedia.org/wiki/B%C3%A9zier_curve)
=======
- **`simulator.py`**: The efficient core of the project. It handles:
  - Pygame rendering loop.
  - Traffic light state machine (Normal Round-Robin vs. Priority Override).
  - Vehicle physics and collision detection.
  - Socket server for receiving spawn requests.

- **`trafficgenerator.py`**: The logic engine. It handles:
  - Random vehicle generation.
  - Client-side queue tracking.
  - Sending spawn commands to the simulator.

## Controls

- The simulation is fully automated.
- **Current Mode** is displayed in the top-left corner (Normal vs. Priority).
- Traffic lights change automatically based on timer logic and queue density.

---
*Created for DSA Queue Simulation Project*
## Screen Record
![Image](https://github.com/user-attachments/assets/95d08ed8-ea8f-4a9b-9a3d-5c8d75ba5f6e)
>>>>>>> 78d8ddaf966b760a300676f53614afc4f94ed06d
