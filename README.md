# Laboratorio de Robótica — UR5 + gripper en ROS 2 Jazzy, Gazebo y MoveIt 2

**Integrantes:** Tomás · Daniela Molina · Santiago Chacón

Solución de las actividades del laboratorio construidas sobre los paquetes base
[`DanielPalominoS/ur5_gripper_packages`](https://github.com/DanielPalominoS/ur5_gripper_packages)
(UR5 con gripper paralelo simple, simulación en Gazebo Harmonic con `ros2_control`).

| # | Actividad | Paquete / evidencia | Video |
|---|-----------|---------------------|-------|
| 1 | Construir la simulación y mover brazo y gripper publicando en tópicos | `src/ur5_gripper_packages` (base) · [`scripts/actividad1_control_topicos.sh`](scripts/actividad1_control_topicos.sh) | [01_control_por_topicos.mp4](media/videos/01_control_por_topicos.mp4) |
| 2 | Nodo que simula una rutina **Pick & Place** (≥3 puntos, abrir/cerrar gripper, mensajes, esperar entradas digitales, activar salidas digitales) | [`src/ur5_pick_place`](src/ur5_pick_place) | [02_pick_and_place.mp4](media/videos/02_pick_and_place.mp4) |
| 3 | Paquete de configuración **MoveIt** generado con el **MoveIt Setup Assistant** + pruebas de planificación en RViz | [`src/ur5_robotiq_moveit_config`](src/ur5_robotiq_moveit_config) · [docs/moveit_setup_assistant.md](docs/moveit_setup_assistant.md) | [03_setup_assistant_pasos.mp4](media/videos/03_setup_assistant_pasos.mp4) · [04_moveit_rviz_planificacion.mp4](media/videos/04_moveit_rviz_planificacion.mp4) |
| 4 | Nodo que ejecuta trayectorias usando el ecosistema MoveIt | [`src/ur5_moveit_executor`](src/ur5_moveit_executor) | [05_moveit_executor_gazebo.mp4](media/videos/05_moveit_executor_gazebo.mp4) |

Hallazgos, problemas encontrados y soluciones: **[docs/hallazgos.md](docs/hallazgos.md)**.
Reporte en LaTeX (editable) y PDF: **[reporte/](reporte/)**.

---

## Estructura

```
ur5_ros2_moveit_lab/            <- la raíz del repositorio ES el workspace de colcon
├── src/
│   ├── ur5_gripper_packages/   paquetes base del profesor (sin modificar)
│   │   ├── ur5_robotiq_description/
│   │   └── ur5_robotiq_bringup/
│   ├── ur5_pick_place/         Actividad 2: rutina Pick & Place + E/S digitales simuladas
│   ├── ur5_robotiq_moveit_config/  Actividad 3: paquete del MoveIt Setup Assistant
│   └── ur5_moveit_executor/    Actividad 4: nodo MoveItPy (planifica y ejecuta en Gazebo)
├── scripts/                    instalación, compilación y lanzamiento de cada actividad
├── docs/                       documentación, capturas del Setup Assistant y logs
├── media/videos/               videos de evidencia
└── reporte/                    reporte LaTeX (main.tex) y PDF
```

## Requisitos

- Ubuntu 24.04 (nativo o **WSL2 con WSLg**) y **ROS 2 Jazzy**.
- Gazebo Harmonic (`ros-jazzy-ros-gz`), `ros2_control`, MoveIt 2 (incluye `moveit_py`).

## Instalación y compilación (WSL)

```bash
cd ~
git clone https://github.com/chaconsantiago966-create/ur5_ros2_moveit_lab.git
cd ur5_ros2_moveit_lab
bash scripts/instalar_dependencias.sh     # apt + rosdep (una sola vez)
bash scripts/compilar.sh                  # colcon build (sin --symlink-install)
source scripts/entorno.sh                 # en cada terminal nueva
```

> En WSLg, si Gazebo o RViz se cierran al abrir por un error de OpenGL, descomente
> `export LIBGL_ALWAYS_SOFTWARE=1` en `scripts/entorno.sh`.

## Ejecución

### Actividad 1 — control por tópicos

```bash
# Terminal 1
ros2 launch ur5_robotiq_bringup sim_gz_sgb.launch.py
# Terminal 2
bash scripts/actividad1_control_topicos.sh
```

Interfaces identificadas (`ros2 topic list`, `ros2 action list`, `ros2 control list_controllers`):

| Elemento | Interfaz | Tipo |
|----------|----------|------|
| Brazo (tópico) | `/scaled_joint_trajectory_controller/joint_trajectory` | `trajectory_msgs/msg/JointTrajectory` |
| Brazo (acción) | `/scaled_joint_trajectory_controller/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` |
| Gripper | `/gripper_controller/commands` | `std_msgs/msg/Float64MultiArray` (`[izq, der]`, 0.004 cerrado … 0.04 abierto) |
| Estado | `/joint_states` | `sensor_msgs/msg/JointState` |

### Actividad 2 — Pick & Place con E/S digitales simuladas

```bash
bash scripts/actividad2_pick_place.sh                     # celda automática
bash scripts/actividad2_pick_place.sh auto_cell:=false    # entradas manuales
```

Con `auto_cell:=false` el robot se detiene en cada `wait_input` hasta que el operador active la entrada:

```bash
ros2 service call /io/di0/set std_srvs/srv/SetBool "{data: true}"   # pieza presente
ros2 service call /io/di1/set std_srvs/srv/SetBool "{data: true}"   # confirmación del PLC
ros2 topic echo /io/state                                           # DI=.... DO=....
```

Detalles en [`src/ur5_pick_place/README.md`](src/ur5_pick_place/README.md).

### Actividad 3 — MoveIt Setup Assistant y pruebas en RViz

```bash
bash scripts/actividad3_moveit_demo.sh        # RViz + plugin MotionPlanning
bash scripts/actividad3_setup_assistant.sh    # abrir/editar el paquete en el asistente
```

### Actividad 4 — trayectorias con MoveIt en Gazebo

```bash
bash scripts/actividad4_moveit_gazebo.sh
```

Lanza Gazebo, `move_group` (configuración del asistente), RViz y el nodo
`moveit_executor` (MoveItPy): `ready` → pose sobre PICK (OMPL) → descenso lineal
(Pilz LIN) → cerrar gripper → subida lineal → pose sobre PLACE esquivando una pared
agregada a la planning scene → abrir gripper → `home`.

## Créditos

- Paquetes base: Daniel Palomino — `ur5_gripper_packages`.
- Modelos del UR5: `ur_description` (Universal Robots).
