#!/usr/bin/env bash
# Actividad 3b: demo de MoveIt (RViz + plugin MotionPlanning, hardware simulado)
source "$(dirname "$0")/entorno.sh"
ros2 launch ur5_robotiq_moveit_config demo.launch.py
