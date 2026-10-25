# ur5_gripper_packages

Resumen
Este repositorio contiene paquetes ROS 2 relacionados con la simulación y la descripción de un UR5 equipado con un gripper paralelo simple. Está organizado en paquetes separados para la descripción (URDF/XACRO) y el bringup (lanzadores, configuraciones y recursos de simulación).

Estructura principal

```
ur5_gripper_packages/
├── ur5_robotiq_bringup/        # Lanzadores y configuraciones para simulación (Gazebo) y visualización (RViz)
├── ur5_robotiq_description/    # XACRO/URDF modulares del UR5 + gripper
└── (otros archivos raíz como .gitignore, etc.)
```

Paquetes incluidos
- [ur5_robotiq_bringup](./ur5_robotiq_bringup/README.md) — lanzadores, configuración de controladores de ejemplo y recursos para ejecutar la simulación y visualizar el robot en RViz.
- [ur5_robotiq_description](./ur5_robotiq_description/README.md) — descripciones URDF/XACRO modulares del UR5 con el gripper; pensado para ser incluido por launchers o por MoveIt.

Dependencias externas y referencias
- Algunos ficheros de este repositorio se basan en o complementan paquetes oficiales de Universal Robots y proyectos relacionados (por ejemplo, `ur_description`, `ur_simulation_gz` y drivers oficiales). Estos paquetes no están incluidos aquí; búsquelos en ROS Index o en los repositorios oficiales de Universal Robots / ROS Industrial si necesita las fuentes o assets originales.
- Dependencias habituales al usar estos paquetes: `xacro`, `robot_state_publisher`, `ros2_control`, `controller_manager`, `gazebo_ros`, `moveit` (opcional para planificación).

Cómo compilar (rápido)
Desde la raíz del workspace que contiene este repositorio:

```bash

# compilar todo el workspace
colcon build

# compilar solo un paquete (ejemplo)
colcon build --packages-select ur5_robotiq_bringup
```

Después de compilar, cargar el overlay de instalación:

```bash
source install/setup.bash
```

Uso rápido (simulación y visualización)
- Lanzar la simulación en Gazebo (desde la raíz del workspace, tras `source install/setup.bash`):

```bash
ros2 launch ur5_robotiq_bringup sim_gz_sgb.launch.py
```

- Abrir RViz con la configuración incluida:

```bash
ros2 launch ur5_robotiq_bringup view_rviz_ur_robotiq.launch.py
```

Generar URDF a partir de XACRO (depuración)
Puede expandir un XACRO a URDF para inspeccionar o depurar:

```bash
ros2 run xacro xacro.py $(ros2 pkg prefix --share ur5_robotiq_description)/urdf/ur_with_gripper_sim.urdf.xacro > /tmp/robot.urdf
check_urdf /tmp/robot.urdf
```

Notas y consideraciones
- Este repositorio separa la descripción del robot (`ur5_robotiq_description`) de los lanzadores y configuraciones (`ur5_robotiq_bringup`) por claridad y reutilización.
- Compruebe que las rutas a mallas (`package://...`) referidas en los XACRO existen en el workspace; de lo contrario RViz/Gazebo no podrán cargar los modelos.
- Si utiliza MoveIt o control real, necesitará paquetes adicionales (configuraciones de planners, controladores, urdf/semantics adicionales) que no forman parte de este repo.

Dónde buscar más información
- Lea los READMEs específicos de cada paquete para detalles precisos y ejemplos: 
  - `ur5_robotiq_bringup/README.md`
  - `ur5_robotiq_description/README.md`
- Para paquetes oficiales del hardware UR (por ejemplo `ur_description`, `universal_robot` drivers o `ur_simulation_gz`), consulte ROS Index o GitHub para las versiones específicas de su distribución ROS 2.
