# ur5_moveit_executor

Nodo `moveit_executor` (MoveItPy) que planifica y ejecuta trayectorias sobre el
UR5 simulado en Gazebo usando el paquete del Setup Assistant
(`ur5_robotiq_moveit_config`).

```bash
ros2 launch ur5_moveit_executor moveit_gazebo.launch.py
```

El launch inicia Gazebo (bringup base + mundo de la celda), `move_group`,
RViz (`rviz/moveit_executor.rviz`) y, a los 30 s, el nodo.

Secuencia: `ready` (estado SRDF) → obstáculo “pared” en la planning scene →
pose TCP sobre PICK (OMPL/RRTConnect) → descenso lineal (Pilz `LIN`) →
cerrar gripper → subida lineal → pose sobre PLACE esquivando la pared →
abrir gripper → `home`.

Configuración:
- `config/moveit_py.yaml`: pipelines `ompl` y `pilz_industrial_motion_planner`, escalas de velocidad.
- `config/moveit_controllers_gazebo.yaml`: MoveIt ejecuta solo el brazo (`scaled_joint_trajectory_controller`); el gripper de la simulación base es un `JointGroupPositionController` y se acciona por tópico.
