# ur5_robotiq_description

Este paquete contiene las descripciones URDF/XACRO de un manipulador UR5 equipado con un gripper paralelo simple. Los archivos están organizados de forma modular para ser incluidos por otros paquetes (simulación, MoveIt, visualización, etc.).

Resumen breve
- Objetivo: proporcionar descripciones modulares (XACRO/URDF) del robot UR5 con gripper para su uso en simulación, planificación y visualización.
- Alcance: solo descripción del robot (URDF/XACRO). No incluye controladores, configuraciones completas de MoveIt ni lanzadores de mundo de Gazebo; esos se encuentran en paquetes de nivel superior (por ejemplo, `ur5_robotiq_bringup`).

Estructura del paquete

```bash
ur5_robotiq_description/
├── CMakeLists.txt
├── include/
│   └── ur5_robotiq_description
├── package.xml
├── README.md
├── src/
└── urdf/
    ├── simple_gripper.xacro
    ├── test.urdf
    ├── ur_with_gripper_base.urdf.xacro
    ├── ur_with_gripper_moveit.urdf.xacro
    └── ur_with_gripper_sim.urdf.xacro
```
Comentarios sobre la estructura
- `urdf/` contiene los archivos fuente XACRO/URDF. Hay wrappers separados para distintos usos: base, MoveIt y simulación.
- `simple_gripper.xacro` define el gripper de forma modular y se incluye desde los wrappers apropiados.

Filosofía XACRO
- Modularidad: separar la definición del gripper y componentes reutilizables para evitar duplicación.
- Wrappers: los archivos `ur_with_gripper_*.xacro` son wrappers orientados a un caso de uso (p. ej. simulación o MoveIt).
- Buenas prácticas: declarar `arg` explícitos en los wrappers y proporcionar valores por defecto; minimizar anidamientos complejos de argumentos.

Dependencias y requisitos
- ROS 2 (usar la distribución del workspace).
- Paquetes habituales necesarios según el uso: `xacro`, `robot_state_publisher`, `gazebo_ros` (si se usa Gazebo), `moveit` (opcional para MoveIt).
- Asegurarse de que `package.xml` declare dependencias de compilación/ejecución para que `rosdep` pueda resolverlas.

Construcción e instalación
Desde la raíz del workspace ROS 2:

```bash

# compilar solo este paquete (desarrollo)
colcon build --packages-select ur5_robotiq_description

# compilar todo el workspace
colcon build
```

Después de compilar, cargar el archivo bash de instalación, necesario para que el paquete sea visible en el entorno:

```bash
source install/setup.bash
```
o
```bash
source ~/<path_al_paquete>/install/setup.bash
```

Generar URDF a partir de XACRO
Para expandir un XACRO a URDF plano (útil para depuración o uso con `robot_state_publisher`):

```bash
ros2 run xacro xacro.py $(ros2 pkg prefix --share ur5_robotiq_description)/urdf/ur_with_gripper_sim.urdf.xacro > /tmp/ur_with_gripper_sim.urdf
```
O aveces simplemente:

```
xacro ur5_robotiq_description/urdf/ur_with_gripper_moveit.urdf.xacro   > /tmp/ur_with_gripper_sim.urdf
```
Luego se puede probar si la expansión del archivo es correcta con `check_urdf /tmp/test_moveit_robot.urdf` que debe generar una salida similar a:
```bash
robot name is: ur
---------- Successfully Parsed XML ---------------
root Link: world has 1 child(ren)
    child(1):  base_link_parent
        child(1):  base_link
            child(1):  base
            child(2):  base_link_inertia
                child(1):  shoulder_link
                    child(1):  upper_arm_link
                        child(1):  forearm_link
                            child(1):  wrist_1_link
                                child(1):  wrist_2_link
                                    child(1):  wrist_3_link
                                        child(1):  flange
                                            child(1):  tool0
                                                child(1):  gripper_base_link
                                                    child(1):  left_finger_link
                                                    child(2):  right_finger_link
                                                child(2):  tool0_tcp
                                        child(2):  ft_frame
```

Si se requieren argumentos de XACRO, pasarlos con `arg:=valor`. Si el orden importa, use `--inorder`.

Escenarios de uso típicos
- Simulación (Gazebo): incluir `ur_with_gripper_sim.urdf.xacro` en el lanzador o wrapper que gestione el spawn del robot en el mundo.
- Planificación (MoveIt): utilizar `ur_with_gripper_moveit.urdf.xacro` como fuente de `robot_description` para MoveIt Setup Assistant o en tiempo de ejecución.
- Visualización o depuración: expandir `ur_with_gripper_base.urdf.xacro` para revisar la estructura sin plugins específicos de simulación.

Limitaciones y consideraciones
- Este paquete solo aporta la descripción del robot; los controladores y la lógica de ejecución pertenecen a otros paquetes.
- Los ficheros XACRO pueden referenciar mallas u otros recursos; estos deben existir en el workspace o en paquetes instalados. Rutas `package://` incorrectas provocan fallos en visualización o spawn.
- Manejo de argumentos XACRO: evitar anidar demasiadas sustituciones de argumentos y establecer valores por defecto en los wrappers superiores.
