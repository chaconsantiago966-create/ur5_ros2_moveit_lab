#!/usr/bin/env bash
# Actividad 4: Gazebo + move_group + RViz + nodo MoveItPy (moveit_executor)
source "$(dirname "$0")/entorno.sh"
ros2 launch ur5_moveit_executor moveit_gazebo.launch.py "$@"
