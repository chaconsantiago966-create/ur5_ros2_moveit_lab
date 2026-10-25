#!/usr/bin/env bash
# Actividad 2: Gazebo + E/S simuladas + RViz + rutina Pick & Place
source "$(dirname "$0")/entorno.sh"
ros2 launch ur5_pick_place pick_place_sim.launch.py "$@"
