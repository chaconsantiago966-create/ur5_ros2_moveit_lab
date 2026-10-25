#!/usr/bin/env bash
# Compila el workspace (la raíz del repositorio es el workspace).
# Nota: NO usar --symlink-install con setuptools >= 80 (ver docs/hallazgos.md).
set -e
source /opt/ros/jazzy/setup.bash
cd "$(dirname "$0")/.."
colcon build
echo; echo "Listo. Ejecute:  source $(pwd)/install/setup.bash"
