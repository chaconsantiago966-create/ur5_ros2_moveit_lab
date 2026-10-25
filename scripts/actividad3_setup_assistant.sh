#!/usr/bin/env bash
# Actividad 3a: abrir el MoveIt Setup Assistant (elegir "Edit Existing" y
# seleccionar src/ur5_robotiq_moveit_config para revisar la configuración).
source "$(dirname "$0")/entorno.sh"
ros2 launch moveit_setup_assistant setup_assistant.launch.py
