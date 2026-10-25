# ur5_pick_place

Rutina **Pick & Place** simulada para el UR5 + gripper del paquete
`ur5_robotiq_bringup`, con **entradas/salidas digitales simuladas**.

```bash
ros2 launch ur5_pick_place pick_place_sim.launch.py            # todo automático
ros2 launch ur5_pick_place pick_place_sim.launch.py auto_cell:=false gazebo_gui:=false
```

## Nodos

### `digital_io_sim`
Emula el módulo de E/S de un controlador de robot o un PLC.

| Interfaz | Tipo | Uso |
|----------|------|-----|
| `/io/di0 … /io/di3` | `std_msgs/Bool` (transient local) | estado de entradas (sensores) |
| `/io/do0 … /io/do3` | `std_msgs/Bool` (transient local) | estado de salidas (actuadores) |
| `/io/di<n>/set` | `std_srvs/SetBool` | forzar una entrada (operador, HMI, pruebas) |
| `/io/do<n>/set` | `std_srvs/SetBool` | el robot activa/desactiva una salida |
| `/io/state` | `std_msgs/String` | resumen `DI=0010 DO=1000` |

Lógica de celda (`auto_cell: true`): DO0 (banda) ON → tras 2 s DI0 (pieza presente) ON;
DO1 (pieza depositada) ON → tras 1.5 s DI1 (confirmación PLC) ON y DI0 OFF;
DI2 (zona de descarga libre) inicia en ON. Con `auto_cell:=false` las entradas
solo cambian por servicio.

### `pick_place_node`
Ejecuta la rutina descrita en [`config/pick_place_routine.yaml`](config/pick_place_routine.yaml):

| Paso | Ejemplo | Acción |
|------|---------|--------|
| `move` | `move:pick@2` | trayectoria articular al punto (acción `FollowJointTrajectory`; o tópico con `use_action:=false`) |
| `gripper` | `gripper:close` | publica en `/gripper_controller/commands` y espera `/joint_states` |
| `message` | `message:Pieza sujeta` | log + `/pick_place/status` |
| `wait_input` | `wait_input:0=ON` | bloquea hasta que `/io/di0` sea `true` |
| `set_output` | `set_output:1=ON` | llama a `/io/do1/set` |
| `wait` | `wait:1.0` | pausa |
| `spawn_part`/`attach`/`detach` | | visualización de la pieza en RViz |

Puntos de interés (6), calculados por cinemática inversa con la herramienta
hacia abajo y verificados con `tf2_echo world tool0_tcp`:

| Punto | TCP (x, y, z) [m] | Operación |
|-------|------------------|-----------|
| `home` | (0.49, 0.11, 0.28) | abrir gripper, activar DO0, esperar DI0 |
| `pick_approach` | (0.45, 0.25, 0.30) | mensaje |
| `pick` | (0.45, 0.25, 0.12) | cerrar gripper, mensaje |
| `inspect` | (0.00, 0.45, 0.35) | mensaje |
| `place_approach` | (0.45, −0.30, 0.30) | esperar DI2 |
| `place` | (0.45, −0.30, 0.12) | abrir gripper, activar DO1, esperar DI1, desactivar DO1 |

Marcadores RViz en `/pick_place/markers` (estaciones, pieza y estado de E/S).
