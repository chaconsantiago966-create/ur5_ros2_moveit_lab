#!/usr/bin/env bash
# Instala las dependencias del laboratorio en Ubuntu 24.04 (WSL2) con ROS 2 Jazzy.
# Requiere tener ROS 2 Jazzy ya configurado (repositorio apt de ROS 2).
set -e
sudo apt update
sudo apt install -y \
  ros-jazzy-desktop ros-jazzy-xacro ros-jazzy-joint-state-publisher-gui \
  ros-jazzy-ur-description ros-jazzy-ur-controllers ros-jazzy-robotiq-description \
  ros-jazzy-ros2-control ros-jazzy-ros2-controllers \
  ros-jazzy-ros-gz ros-jazzy-gz-ros2-control \
  ros-jazzy-moveit ros-jazzy-moveit-py ros-jazzy-moveit-setup-assistant \
  ros-jazzy-moveit-planners-ompl ros-jazzy-pilz-industrial-motion-planner \
  python3-colcon-common-extensions python3-rosdep
# rosdep (opcional, resuelve lo que falte a partir de los package.xml)
[ -f /etc/ros/rosdep/sources.list.d/20-default.list ] || sudo rosdep init || true
rosdep update
cd "$(dirname "$0")/.."
rosdep install --from-paths src --ignore-src -y --rosdistro jazzy || true
echo "Dependencias instaladas."
