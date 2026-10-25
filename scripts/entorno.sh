# Uso:  source scripts/entorno.sh
source /opt/ros/jazzy/setup.bash
_WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$_WS/install/setup.bash"
# En WSLg, si Gazebo o RViz se cierran al abrir (error de OpenGL/ogre2),
# descomente la siguiente línea para usar renderizado por software:
# export LIBGL_ALWAYS_SOFTWARE=1
