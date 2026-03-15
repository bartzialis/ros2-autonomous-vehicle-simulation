# ROS2 Autonomous Vehicle Simulation

A simulation environment developed for testing autonomous racing vehicle behavior in a Formula Student Driverless context.

The project simulates a racing vehicle navigating through a cone-based track and integrates ROS2 communication for vehicle control, telemetry and visualization.

## Features

- 2D vehicle dynamics simulation
- Cone-based racing track representation
- Vehicle acceleration, steering and collision handling
- Teleoperation control via keyboard
- ROS2 publisher/subscriber architecture
- Vehicle telemetry monitoring
- 3D visualization using RViz2 / Foxglove

## System Architecture

Simulation → ROS2 Topics → Visualization

The simulation publishes vehicle state data and receives control commands through ROS2 communication.

## ROS Topics

### Published Topics

- Vehicle position
- Vehicle velocity
- Lap counter
- Gear state
- Vehicle pose
- Odometry data
- Path visualization
- Cone positions (PointCloud2)

### Subscribed Topics

- Throttle commands
- Steering commands
- Respawn commands

## Technologies

- Python
- ROS2
- Pygame
- RViz2
- Foxglove
- Linux

## Project Structure
