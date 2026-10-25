#!/usr/bin/env bash
# Actividad 1: ejecutar en una SEGUNDA terminal con la simulación ya abierta:
#   Terminal 1:  ros2 launch ur5_robotiq_bringup sim_gz_sgb.launch.py
#   Terminal 2:  bash scripts/actividad1_control_topicos.sh
source "$(dirname "$0")/entorno.sh"
J="['shoulder_pan_joint','shoulder_lift_joint','elbow_joint','wrist_1_joint','wrist_2_joint','wrist_3_joint']"
arm(){ ros2 topic pub --once /scaled_joint_trajectory_controller/joint_trajectory \
  trajectory_msgs/msg/JointTrajectory "{joint_names: $J, points: [{positions: [$1], time_from_start: {sec: 3}}]}"; }
grip(){ ros2 topic pub --once /gripper_controller/commands std_msgs/msg/Float64MultiArray "{data: [$1, $1]}"; }
ros2 control list_controllers
arm "0.8, -1.2, 1.4, -1.77, -1.57, 0.0"; sleep 4
grip 0.04; sleep 2; grip 0.02; sleep 2; grip 0.004; sleep 2
arm "-0.8, -1.8, 1.9, -1.67, -1.57, 1.0"; sleep 4
arm "0.0, -1.57, 1.57, -1.57, -1.57, 0.0"; grip 0.04
