#!/bin/bash

# Check usage
if [ $# -ne 2 ]; then
  echo "Usage: $0 <PORT1> <PORT2>"
  exit 1
fi

PORT1=$1
PORT2=$2

echo "[INFO] Building workspace..."
cd ~/Robocon-25_codes/joy_serial_ws || { echo "Directory not found"; exit 1; }
colcon build

echo "[INFO] Waiting for build to settle..."
sleep 3

echo "[INFO] Sourcing ROS2 setup..."
source install/setup.bash

# Run joy_node
echo "[INFO] Launching joy_node..."
gnome-terminal --tab --title="joy_node" -- bash -c "source install/setup.bash && ros2 run joy joy_node --ros-args -p deadzone:=0.0; exec bash"

sleep 1

# Start minicom for PORT1
echo "[INFO] Starting minicom on /dev/tty$PORT1..."
gnome-terminal --tab --title="minicom $PORT1" -- bash -c "minicom -D /dev/tty$PORT1 -b 115200; exec bash"

sleep 1

# Start minicom for PORT2
echo "[INFO] Starting minicom on /dev/tty$PORT2..."
gnome-terminal --tab --title="minicom $PORT2" -- bash -c "minicom -D /dev/tty$PORT2 -b 115200; exec bash"

sleep 3

# Start joy_to_serial for PORT1
echo "[INFO] Starting joy_to_serial on /dev/tty$PORT1..."
gnome-terminal --tab --title="joy_serial $PORT1" -- bash -c "source install/setup.bash && ros2 run joy_serial_bridge joy_to_serial --ros-args -p dev:=/dev/tty$PORT1 -p baud:=115200; exec bash"

sleep 1

# Start joy_to_serial for PORT2
echo "[INFO] Starting joy_to_serial on /dev/tty$PORT2..."
gnome-terminal --tab --title="joy_serial $PORT2" -- bash -c "source install/setup.bash && ros2 run joy_serial_bridge joy_to_serial --ros-args -p dev:=/dev/tty$PORT2 -p baud:=115200; exec bash"