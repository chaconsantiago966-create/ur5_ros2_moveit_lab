#!/usr/bin/env python3
"""Ejecución de trayectorias con el ecosistema MoveIt 2 (MoveItPy).

Usa la configuración generada con el MoveIt Setup Assistant
(paquete ur5_robotiq_moveit_config) para planificar y ejecutar sobre el
UR5 simulado en Gazebo:

  1. Planifica a un estado con nombre del SRDF ("ready").
  2. Agrega un obstáculo (CollisionObject) a la escena de planificación.
  3. Planifica a una pose cartesiana del TCP (tool0_tcp) sobre la estación
     PICK, esquivando el obstáculo (OMPL / RRTConnect).
  4. Desciende en línea recta con el planificador Pilz (LIN).
  5. Cierra el gripper (tópico /gripper_controller/commands).
  6. Lleva la pieza a la estación PLACE (pose objetivo, OMPL).
  7. Abre el gripper y vuelve a "home" (estado con nombre del SRDF).

Cada plan se ejecuta con MoveItPy.execute(), que envía la trayectoria al
controlador scaled_joint_trajectory_controller (FollowJointTrajectory).
"""
import time

import rclpy
from rclpy.node import Node
from rclpy.logging import get_logger

from geometry_msgs.msg import Pose, PoseStamped
from moveit.core.robot_state import RobotState  # noqa: F401
from moveit.planning import MoveItPy, PlanRequestParameters
from moveit_msgs.msg import CollisionObject, PlanningScene
from shape_msgs.msg import SolidPrimitive
from std_msgs.msg import Float64MultiArray

GROUP = 'ur_arm'
TCP = 'tool0_tcp'
LOG = get_logger('moveit_executor')

# Orientación "herramienta hacia abajo" medida con tf2_echo world tool0_tcp
DOWN = (0.0, 1.0, 0.0, 0.0)  # x, y, z, w


def pose_goal(x, y, z, q=DOWN, frame='world'):
    ps = PoseStamped()
    ps.header.frame_id = frame
    ps.pose.position.x, ps.pose.position.y, ps.pose.position.z = x, y, z
    (ps.pose.orientation.x, ps.pose.orientation.y,
     ps.pose.orientation.z, ps.pose.orientation.w) = q
    return ps


class Executor:

    def __init__(self):
        self.robot = MoveItPy(node_name='moveit_py')
        self.arm = self.robot.get_planning_component(GROUP)
        self.helper = Node('moveit_executor_helper')
        self.gripper_pub = self.helper.create_publisher(
            Float64MultiArray, '/gripper_controller/commands', 10)
        self.scene_pub = self.helper.create_publisher(
            PlanningScene, '/planning_scene', 10)
        self.lin = PlanRequestParameters(self.robot, 'pilz_lin')
        LOG.info('MoveItPy listo - grupo de planificación: ' + GROUP)
        time.sleep(3.0)  # deja conectar los clientes de acción de MoveIt

    # --------------------------------------------------------------
    def add_obstacle(self):
        """Pared baja (25 cm) entre las estaciones PICK y PLACE.

        Debe quedar por debajo del brazo en las poses home/ready; de lo
        contrario MoveIt rechaza planificar (CheckStartStateCollision).
        """
        psm = self.robot.get_planning_scene_monitor()
        with psm.read_write() as scene:
            co = CollisionObject()
            co.header.frame_id = 'world'
            co.id = 'pared'
            box = SolidPrimitive(type=SolidPrimitive.BOX,
                                 dimensions=[0.30, 0.04, 0.25])
            p = Pose()
            p.position.x, p.position.y, p.position.z = 0.45, -0.03, 0.125
            p.orientation.w = 1.0
            co.primitives.append(box)
            co.primitive_poses.append(p)
            co.operation = CollisionObject.ADD
            scene.apply_collision_object(co)
            scene.current_state.update()
        # La escena de MoveItPy es local a este nodo: se publica también
        # como diferencia en /planning_scene para que move_group y RViz
        # (display MotionPlanning) muestren el obstáculo.
        diff = PlanningScene(is_diff=True)
        diff.world.collision_objects.append(co)
        for _ in range(3):
            self.scene_pub.publish(diff)
            time.sleep(0.2)
        LOG.info('[ESCENA] Obstáculo "pared" agregado a la planning scene')

    def gripper(self, value, label):
        LOG.info(f'[GRIPPER] {label} ({value} m)')
        self.gripper_pub.publish(Float64MultiArray(data=[value, value]))
        time.sleep(1.5)

    def plan_and_execute(self, label, params=None):
        LOG.info(f'[PLAN] {label} ...')
        self.arm.set_start_state_to_current_state()
        t0 = time.time()
        result = self.arm.plan(single_plan_parameters=params) if params \
            else self.arm.plan()
        if not result:
            LOG.error(f'[PLAN] {label}: FALLÓ la planificación')
            return False
        n = len(result.trajectory.get_robot_trajectory_msg()
                .joint_trajectory.points)
        LOG.info(f'[PLAN] {label}: OK en {time.time() - t0:.2f}s '
                 f'({n} puntos) -> ejecutando')
        # execute() devuelve un ExecutionStatus; se reintenta si el cliente
        # de acción aún no estaba conectado al controlador (ABORTED inmediato).
        for intento in range(1, 4):
            status = self.robot.execute(result.trajectory, controllers=[])
            st = str(getattr(status, 'status', status))
            if 'SUCCEEDED' in st.upper():
                LOG.info(f'[EXEC] {label}: completado ({st})')
                return True
            LOG.warn(f'[EXEC] {label}: estado {st} (intento {intento}/3), '
                     'reintentando en 2 s')
            time.sleep(2.0)
            self.arm.set_start_state_to_current_state()
            result = self.arm.plan(single_plan_parameters=params) if params \
                else self.arm.plan()
            if not result:
                break
        LOG.error(f'[EXEC] {label}: no se pudo ejecutar')
        return False

    # --------------------------------------------------------------
    def run(self):
        self.gripper(0.04, 'abrir')

        # En Gazebo el robot arranca con todas las articulaciones en 0
        # (brazo estirado a ras del piso): primero se lleva a "ready" y
        # luego se agrega el obstáculo, para no iniciar en colisión.
        self.arm.set_goal_state(configuration_name='ready')
        if not self.plan_and_execute('estado con nombre "ready"'):
            LOG.error('No se alcanzó "ready"; se aborta la secuencia')
            return
        self.add_obstacle()

        self.arm.set_goal_state(pose_stamped_msg=pose_goal(0.45, 0.25, 0.25),
                                pose_link=TCP)
        self.plan_and_execute('pose TCP sobre PICK (0.45, 0.25, 0.25)')

        self.arm.set_goal_state(pose_stamped_msg=pose_goal(0.45, 0.25, 0.12),
                                pose_link=TCP)
        if not self.plan_and_execute('descenso lineal Pilz LIN a z=0.12',
                                     self.lin):
            self.plan_and_execute('descenso (OMPL, respaldo)')

        self.gripper(0.02, 'cerrar')

        self.arm.set_goal_state(pose_stamped_msg=pose_goal(0.45, 0.25, 0.30),
                                pose_link=TCP)
        self.plan_and_execute('subida a z=0.30', self.lin)

        self.arm.set_goal_state(pose_stamped_msg=pose_goal(0.45, -0.30, 0.20),
                                pose_link=TCP)
        self.plan_and_execute('pose sobre PLACE (0.45, -0.30, 0.20) '
                              'esquivando la pared')

        self.gripper(0.04, 'abrir')

        self.arm.set_goal_state(configuration_name='home')
        self.plan_and_execute('estado con nombre "home"')
        LOG.info('Secuencia MoveIt finalizada')


def main():
    rclpy.init()
    ex = Executor()
    try:
        ex.run()
    finally:
        time.sleep(1.0)
        ex.helper.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
