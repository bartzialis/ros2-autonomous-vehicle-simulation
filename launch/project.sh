# Bartzialis 

#!/bin/bash

# Open new terminal and run the script
gnome-terminal -- bash -c "python3 /home/giannis/Centaurus/proj1/proj1.py; exec bash"
gnome-terminal -- bash -c "python3 /home/giannis/Centaurus/proj1/teleop.py; exec bash"
gnome-terminal -- bash -c "python3 /home/giannis/Centaurus/proj1/subscriber.py; exec bash"
gnome-terminal -- bash -c "ros2 launch foxglove_bridge foxglove_bridge_launch.xml"
