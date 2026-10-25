# Hallazgos, dificultades y soluciones

Registro de los problemas encontrados durante el laboratorio, cómo se
diagnosticaron y la alternativa aplicada (incluidas las que no funcionaron).
Los logs completos están en [`docs/logs/`](logs/).

## Entorno de trabajo

| Elemento | Versión usada |
|----------|---------------|
| SO | Ubuntu 24.04 (contenedor Linux x86_64, 2 núcleos, 8 GB RAM, sin GPU) |
| ROS 2 | Jazzy (distribución RoboStack / conda-forge, `ros-jazzy-desktop 0.11`) |
| Gazebo | Harmonic (`ros_gz 1.0.24`, `gz_ros2_control 1.2.20`) |
| MoveIt 2 | 2.12.4 (`moveit`, `moveit_py`, `moveit_setup_assistant`) |
| UR | `ur_description 3.3`, `ur_controllers 3.9` |
| Render | Mesa llvmpipe (OpenGL 4.5 por software) en pantalla virtual Xvfb |

Todos los resultados se verificaron ejecutando la simulación (logs y videos
en este repositorio).

---

### H1. No fue posible instalar ROS 2 desde `packages.ros.org`
- **Síntoma:** `curl: (6) Could not resolve host: packages.ros.org` / `CONNECT tunnel failed, response 403` en el equipo de ejecución.
- **Alternativa aplicada:** instalar ROS 2 Jazzy, Gazebo y MoveIt con **RoboStack** (`micromamba create -n ros -c robostack-jazzy -c conda-forge ros-jazzy-desktop ros-jazzy-moveit …`). Todos los paquetes requeridos existen en RoboStack, incluidos `ur_description`, `ur_controllers`, `gz_ros2_control` y `moveit_py`.
- **En WSL** se recomienda la instalación estándar por `apt` (`scripts/instalar_dependencias.sh`).

### H2. `colcon build --symlink-install` falla en paquetes Python
- **Síntoma:** `error: option --editable not recognized` al compilar `ur5_robotiq_bringup`.
- **Causa:** setuptools ≥ 80 (aquí 84.2.1) eliminó el modo `develop` que usa colcon para los enlaces simbólicos.
- **Solución:** compilar sin `--symlink-install` (`scripts/compilar.sh`). Alternativa: `pip install "setuptools<80"`.

### H3. `xacro` falla al expandir el modelo de simulación a mano
- **Síntoma:** `error: Undefined substitution argument name` con `ur_with_gripper_sim.urdf.xacro`.
- **Causa:** el atributo `name="$(arg name)"` del `<robot>` se evalúa antes del `<xacro:arg>`.
- **Solución:** pasar `name:=ur` (el launch del repositorio base ya lo hace). `check_urdf` confirma la cadena `world → base_link_parent → … → tool0 → gripper_base_link / tool0_tcp`.

### H4. Nombres de tópicos inválidos para las E/S digitales
- **Síntoma:** `InvalidTopicNameException` al crear `/io/di/0`.
- **Causa:** en ROS 2 ningún segmento de un nombre de tópico puede empezar con un dígito.
- **Solución:** `/io/di0 … /io/di3`, `/io/do0 … /io/do3` y servicios `/io/di0/set`, `/io/do0/set`.

### H5. El MoveIt Setup Assistant se cierra al escribir la ruta del URDF
- **Síntoma:** al escribir la ruta del `.xacro` letra por letra el asistente aborta (`std::length_error` en `rdf_loader::RDFLoader::loadFileToString`). Log: [`logs/msa_crash_ruta.log`](logs/msa_crash_ruta.log).
- **Causa:** `StartScreenWidget::onUrdfPathChanged` intenta cargar el archivo en **cada** cambio del campo; cuando la ruta parcial coincide con un **directorio** existente, la lectura falla con una excepción no capturada.
- **Solución:** pegar la ruta completa de una sola vez (o usar *Browse*). Alternativa: lanzar `moveit_setup_assistant --urdf_path <archivo>`.

### H6. Virtual joint de la guía vs. URDF del repositorio
- La guía pide un virtual joint `world_joint` con hijo `base_link_parent`, pero `ur_with_gripper_moveit.urdf.xacro` ya define el link `world` y la unión fija `world_to_base → base_link_parent`. El asistente solo ofrece como hijo el link raíz (`world`).
- **Decisión:** no agregar virtual joint (sería redundante y duplicaría el frame `world`). El asistente lo recuerda al generar (“No virtual joints have been added”) y se aceptó.

### H7. End effector: el grupo padre no contiene `tool0`
- **Síntoma:** “The specified parent group 'ur_arm' must contain the specified parent link 'tool0'”.
- **Causa:** `ur_arm` se definió por articulaciones (las 6 revolutas), por lo que su último link es `wrist_3_link`; `tool0` cuelga de uniones fijas fuera del grupo.
- **Solución (igual a la guía):** dejar *Parent Group* vacío. Efecto: aviso `Could not identify parent group for end-effector 'arm_eef'` (sin impacto). Alternativa: definir `ur_arm` como cadena `base_link → tool0`.

### H8. La planificación falla por falta de límites de aceleración
- **Síntoma (demo de RViz):** `No acceleration limit was defined for joint shoulder_pan_joint! … Response adapter 'AddTimeOptimalParameterization' failed`. Video: [04a_moveit_rviz_error_aceleracion.mp4](../media/videos/04a_moveit_rviz_error_aceleracion.mp4), log: [`logs/demo_error_totg.log`](logs/demo_error_totg.log).
- **Causa:** el asistente genera `has_acceleration_limits: false` y `max_acceleration: 0`; en MoveIt 2 Jazzy el parametrizador temporal exige aceleraciones.
- **Solución:** `config/joint_limits.yaml` con `has_acceleration_limits: true` (5 rad/s² brazo, 1 m/s² dedos). Commit separado de la salida original del asistente.

### H9. Posiciones iniciales fuera de límites
- `initial_positions.yaml` se genera con 0 en todas las articulaciones, pero los dedos tienen límite inferior 0.002 m. Se cambió a HOME `[0, -1.57, 1.57, -1.57, -1.57, 0]` y gripper abierto (0.04).

### H10. Controlador del gripper
- El asistente genera `position_controllers/GripperActionController` con **un solo** joint (`joint: gripper_finger_joint`): en el demo el dedo derecho no es comandado por ese controlador (el gripper simple tiene dos prismáticas independientes, sin `mimic`).
- En Gazebo el repositorio base usa `JointGroupPositionController` (`/gripper_controller/commands`), que no ofrece la acción `GripperCommand`. Por eso en la Actividad 4 MoveIt ejecuta **solo el brazo** (`config/moveit_controllers_gazebo.yaml`) y el gripper se acciona por tópico.
- Alternativas para un trabajo futuro: agregar `mimic` al dedo derecho y usar `parallel_gripper_action_controller`, o un `JointTrajectoryController` para el gripper.

### H11. El robot inicia en colisión con el obstáculo en Gazebo
- **Síntoma:** `CheckStartStateCollision failed … forearm_link - pared`. Log: [`logs/moveit_executor_error_colision_inicial.log`](logs/moveit_executor_error_colision_inicial.log).
- **Causa:** en Gazebo todas las articulaciones arrancan en 0 (brazo estirado a ras del piso), dentro de la pared.
- **Solución:** mover primero a `ready` y luego insertar el obstáculo; la pared se dejó en 25 cm de alto.

### H12. `MoveItPy.execute()` devuelve ABORTED inmediatamente (intermitente)
- **Síntoma:** `Action client not connected to action server: scaled_joint_trajectory_controller/follow_joint_trajectory` y `Completed trajectory execution with status ABORTED`, mientras el nodo informaba “completado”.
- **Causa:** condición de carrera al iniciar; el código no revisaba el `ExecutionStatus`.
- **Solución:** esperar 3 s tras crear `MoveItPy`, verificar `status == SUCCEEDED` y reintentar (replanificando) hasta 3 veces.

### H13. El obstáculo no aparecía en RViz
- La planning scene de `MoveItPy` es local al nodo; `move_group`/RViz no la ven. Se publica además un `moveit_msgs/PlanningScene` (`is_diff: true`) en `/planning_scene`.

### H14. Rendimiento sin GPU
- Con render por software el *real time factor* de Gazebo fue 45–65 % y RViz 3–30 fps. No altera los resultados (los controladores usan tiempo de simulación) pero las trayectorias se ven más lentas en los videos.

### H15. Detalles menores
- RViz 2 separa visualmente las palabras de un marcador `TEXT_VIEW_FACING`; el estado de E/S se muestra sin espacios (`DI=0010|DO=1000`).
- El archivo `.setup_assistant` generado contiene la clave `control_xacro` duplicada (comportamiento del asistente; no afecta la carga).
- La “pieza” del Pick & Place es simulada: en RViz se adjunta al TCP al cerrar el gripper (no hay física de agarre en Gazebo). Alternativa considerada: plugin `DetachableJoint` de Gazebo.
