# Traffic Queue Simulator

A real-time traffic intersection simulation built with Python and Pygame. This project demonstrates the application of Data Structures and Algorithms (DSA), specifically **Queues** and **Priority Logic**, to efficiently manage traffic flow.

## Overview

The system simulates a 4-way intersection implementation using a client-server architecture:
- **Simulator (Server):** Renders the visual environment, manages traffic lights, and handles vehicle physics.
- **Traffic Generator (Client):** Generates vehicle data based on stochastic patterns and sends it to the simulator via TCP sockets.

## Key Features

- **Queue-Based Traffic Management:** Vehicles are processed using FIFO (First-In-First-Out) queues, ensuring fair processing for standard traffic.
- **Dynamic Priority System:** 
  - The system continuously monitors lane density.
  - If a lane exceeds a critical threshold (e.g., >10 vehicles), **Priority Mode** is activated.
  - The traffic light logic adapts to give the congested lane a green signal until traffic subsides.
- **Smooth Visuals:**
  - Modern, clean UI with a grass backdrop and dark asphalt roads.
  - Tangent-based Bezier curve calculations for fluid, realistic turning animations.
  - Corner-mounted traffic lights and on-screen status indicators.
- **Networking:** Robust TCP/IP communication allows the generator and simulator to run as independent processes.

## Requirements

- Python 3.x
- Pygame

## Installation & Usage

1. **Install Dependencies:**
   ```bash
   pip install pygame
   ```

2. **Run the Simulator (Server):**
   Start the visualization window first.
   ```bash
   python simulator.py
   ```
   *The server will start listening on port 5000.*

3. **Run the Traffic Generator (Client):**
   Open a new terminal and run:
   ```bash
   python trafficgenerator.py
   ```
   *Vehicles will begin spawning automatically using the default speed settings.*

## Project Structure

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
