#!/usr/bin/env python3
"""Rutina Pick & Place para el UR5 + gripper simple (simulación Gazebo).

La rutina se describe como una lista de pasos en un archivo YAML
(config/pick_place_routine.yaml). Cada paso es uno de:

  move         -> mueve el brazo a un punto de interés (posiciones articulares)
  gripper      -> abre / cierra el gripper
  message      -> mensaje informativo (log + tópico /pick_place/status)
  wait_input   -> espera a que una entrada digital DI<n> tome un valor
  set_output   -> activa / desactiva una salida digital DO<n>
  wait         -> pausa fija en segundos
  attach/detach-> (visual) la pieza en RViz se une / separa del TCP

Interfaces ROS utilizadas (identificadas con `ros2 topic list` /
`ros2 action list` sobre la simulación del repositorio base):
  * Brazo  : acción  /scaled_joint_trajectory_controller/follow_joint_trajectory
             (control_msgs/action/FollowJointTrajectory). Opcionalmente el
             tópico /scaled_joint_trajectory_controller/joint_trajectory
             (trajectory_msgs/JointTrajectory) con use_action:=false.
  * Gripper: tópico  /gripper_controller/commands (std_msgs/Float64MultiArray)
  * Estado : tópico  /joint_states (sensor_msgs/JointState)
  * I/O    : tópicos /io/di<n>, /io/do<n> (std_msgs/Bool) y servicios
             /io/do<n>/set (std_srvs/SetBool) del nodo digital_io_sim.
"""
import threading
import time

import rclpy
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy

from builtin_interfaces.msg import Duration, Time
from control_msgs.action import FollowJointTrajectory
from geometry_msgs.msg import Point
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool, ColorRGBA, Float64MultiArray, String
from std_srvs.srv import SetBool
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from visualization_msgs.msg import Marker, MarkerArray

ARM_JOINTS = ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
              'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']
GRIPPER_JOINTS = ['gripper_finger_joint', 'right_finger_joint']


def _dur(sec):
    s = int(sec)
    return Duration(sec=s, nanosec=int((sec - s) * 1e9))


class PickPlaceNode(Node):

    def __init__(self):
        super().__init__('pick_place_node')
        cb = ReentrantCallbackGroup()

        # ---------------- parámetros ----------------
        self.declare_parameter('use_action', True)
        self.declare_parameter('cycles', 1)
        self.declare_parameter('default_move_time', 3.0)
        self.declare_parameter('gripper_open', 0.04)
        self.declare_parameter('gripper_close', 0.02)
        self.declare_parameter('point_names', [''])
        self.declare_parameter('step_list', [''])
        self.declare_parameter('stations.pick', [0.45, 0.25, 0.12])
        self.declare_parameter('stations.place', [0.45, -0.30, 0.12])
        self.declare_parameter('part_size', 0.04)

        self.points = {}
        for name in self.get_parameter('point_names').value:
            if not name:
                continue
            self.declare_parameter(f'points.{name}', [0.0] * 6)
            self.points[name] = list(
                self.get_parameter(f'points.{name}').value)
        self.steps = [s for s in self.get_parameter('step_list').value if s]

        # ---------------- interfaces ----------------
        self.arm_action = ActionClient(
            self, FollowJointTrajectory,
            '/scaled_joint_trajectory_controller/follow_joint_trajectory',
            callback_group=cb)
        self.arm_topic = self.create_publisher(
            JointTrajectory,
            '/scaled_joint_trajectory_controller/joint_trajectory', 10)
        self.gripper_pub = self.create_publisher(
            Float64MultiArray, '/gripper_controller/commands', 10)
        self.status_pub = self.create_publisher(
            String, '/pick_place/status', 10)
        self.marker_pub = self.create_publisher(
            MarkerArray, '/pick_place/markers', 10)

        self.joint_pos = {}
        self.create_subscription(JointState, '/joint_states',
                                 self._on_js, 50, callback_group=cb)

        io_qos = QoSProfile(depth=1,
                            durability=DurabilityPolicy.TRANSIENT_LOCAL,
                            reliability=ReliabilityPolicy.RELIABLE)
        self.di = {}
        self.do = {}
        self.io_text = ''
        for i in range(8):
            self.create_subscription(
                Bool, f'/io/di{i}',
                lambda m, i=i: self.di.__setitem__(i, m.data), io_qos,
                callback_group=cb)
            self.create_subscription(
                Bool, f'/io/do{i}',
                lambda m, i=i: self.do.__setitem__(i, m.data), io_qos,
                callback_group=cb)
        self.create_subscription(String, '/io/state',
                                 lambda m: setattr(self, 'io_text', m.data),
                                 io_qos, callback_group=cb)
        self._do_clients = {}

        # ---------------- estado visual ----------------
        self.part_attached = False
        self.part_pos = list(self.get_parameter('stations.pick').value)
        self.part_visible = False
        self.last_status = 'Esperando inicio'
        self.create_timer(0.1, self._publish_markers, callback_group=cb)

    # ==================================================================
    # Callbacks
    def _on_js(self, msg):
        for n, p in zip(msg.name, msg.position):
            self.joint_pos[n] = p

    # ==================================================================
    # Primitivas
    def info(self, text):
        self.last_status = text
        self.get_logger().info(f'[MENSAJE] {text}')
        self.status_pub.publish(String(data=text))

    def move(self, point, t=None):
        q = self.points[point]
        t = t or self.get_parameter('default_move_time').value
        self.get_logger().info(f'[MOVE] -> {point} {q} ({t:.1f}s)')
        self.last_status = f'Moviendo a {point}'
        traj = JointTrajectory()
        traj.joint_names = ARM_JOINTS
        traj.points = [JointTrajectoryPoint(positions=q,
                                            time_from_start=_dur(t))]
        if self.get_parameter('use_action').value:
            if not self.arm_action.wait_for_server(timeout_sec=10.0):
                raise RuntimeError('Servidor de acción del brazo no disponible')
            goal = FollowJointTrajectory.Goal(trajectory=traj)
            fut = self.arm_action.send_goal_async(goal)
            handle = self._wait_future(fut, 10.0)
            if not handle.accepted:
                raise RuntimeError('Trayectoria rechazada')
            res = self._wait_future(handle.get_result_async(), t + 10.0)
            if res.result.error_code != 0:
                self.get_logger().warn(
                    f'Resultado trayectoria: código {res.result.error_code} '
                    f'{res.result.error_string}')
        else:
            self.arm_topic.publish(traj)
            self._wait_joints(dict(zip(ARM_JOINTS, q)), 0.01, t + 5.0)

    def gripper(self, state):
        v = self.get_parameter(f'gripper_{state}').value
        self.get_logger().info(f'[GRIPPER] {state.upper()} ({v:.3f} m)')
        self.last_status = f'Gripper: {"abriendo" if state == "open" else "cerrando"}'
        self.gripper_pub.publish(Float64MultiArray(data=[v, v]))
        self._wait_joints({j: v for j in GRIPPER_JOINTS}, 0.003, 5.0)

    def wait_input(self, idx, value=True, timeout=60.0):
        self.get_logger().info(
            f'[WAIT DI{idx}] esperando {"ON" if value else "OFF"} ...')
        self.last_status = f'Esperando DI{idx} = {"ON" if value else "OFF"}'
        t0 = time.time()
        while rclpy.ok():
            if self.di.get(idx) == value:
                self.get_logger().info(f'[WAIT DI{idx}] condición cumplida')
                return
            if timeout and time.time() - t0 > timeout:
                raise TimeoutError(f'Timeout esperando DI{idx}')
            time.sleep(0.05)

    def set_output(self, idx, value=True):
        if idx not in self._do_clients:
            self._do_clients[idx] = self.create_client(
                SetBool, f'/io/do{idx}/set')
        cli = self._do_clients[idx]
        if not cli.wait_for_service(timeout_sec=10.0):
            raise RuntimeError(f'Servicio /io/do{idx}/set no disponible')
        res = self._wait_future(cli.call_async(SetBool.Request(data=value)), 5)
        self.get_logger().info(f'[SET DO{idx}] {res.message}')
        self.last_status = f'Salida DO{idx} = {"ON" if value else "OFF"}'

    # ------------------------------------------------------------------
    def _wait_future(self, fut, timeout):
        t0 = time.time()
        while not fut.done():
            if time.time() - t0 > timeout:
                raise TimeoutError('Timeout esperando respuesta')
            time.sleep(0.01)
        return fut.result()

    def _wait_joints(self, target, tol, timeout):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if all(abs(self.joint_pos.get(j, 1e9) - v) < tol
                   for j, v in target.items()):
                return True
            time.sleep(0.05)
        self.get_logger().warn('Articulaciones no alcanzaron el objetivo '
                               '(tolerancia) - se continúa')
        return False

    # ==================================================================
    # Intérprete de la rutina
    def run_step(self, step):
        kind, _, arg = step.partition(':')
        kind, arg = kind.strip(), arg.strip()
        if kind == 'move':
            name, _, t = arg.partition('@')
            self.move(name.strip(), float(t) if t else None)
        elif kind == 'gripper':
            self.gripper(arg)
        elif kind == 'message':
            self.info(arg)
        elif kind == 'wait_input':
            idx, _, val = arg.partition('=')
            self.wait_input(int(idx), val.strip().upper() != 'OFF')
        elif kind == 'set_output':
            idx, _, val = arg.partition('=')
            self.set_output(int(idx), val.strip().upper() != 'OFF')
        elif kind == 'wait':
            self.last_status = f'Pausa {arg}s'
            time.sleep(float(arg))
        elif kind == 'spawn_part':
            self.part_pos = list(self.get_parameter('stations.pick').value)
            self.part_visible = True
        elif kind == 'attach':
            self.part_attached = True
        elif kind == 'detach':
            self.part_attached = False
            self.part_pos = list(self.get_parameter('stations.place').value)
        else:
            raise ValueError(f'Paso desconocido: {step}')

    def run(self):
        # Esperar a tener /joint_states
        while rclpy.ok() and not all(j in self.joint_pos for j in ARM_JOINTS):
            time.sleep(0.1)
        cycles = self.get_parameter('cycles').value
        for c in range(1, cycles + 1):
            self.info(f'===== Ciclo {c}/{cycles} =====')
            for i, step in enumerate(self.steps, 1):
                self.get_logger().info(f'Paso {i}/{len(self.steps)}: {step}')
                self.run_step(step)
        self.info('Rutina Pick & Place finalizada')

    # ==================================================================
    # Visualización (RViz)
    def _publish_markers(self):
        now = Time()  # stamp 0 -> RViz usa la última TF disponible
        arr = MarkerArray()

        def mk(mid, mtype, frame='world'):
            m = Marker()
            m.header.frame_id = frame
            m.header.stamp = now
            m.ns = 'pick_place'
            m.id = mid
            m.type = mtype
            m.action = Marker.ADD
            m.pose.orientation.w = 1.0
            return m

        size = self.get_parameter('part_size').value
        for mid, key, color, label in [
                (0, 'pick', (0.1, 0.7, 0.2), 'PICK'),
                (1, 'place', (0.2, 0.4, 0.9), 'PLACE')]:
            x, y, z = self.get_parameter(f'stations.{key}').value
            h = z - size / 2
            m = mk(mid, Marker.CUBE)
            m.pose.position = Point(x=x, y=y, z=h / 2)
            m.scale.x, m.scale.y, m.scale.z = 0.20, 0.20, h
            m.color = ColorRGBA(r=color[0], g=color[1], b=color[2], a=0.8)
            arr.markers.append(m)
            t = mk(mid + 10, Marker.TEXT_VIEW_FACING)
            t.pose.position = Point(x=x, y=y, z=0.02)
            t.pose.position.z = h + 0.12
            t.scale.z = 0.05
            t.color = ColorRGBA(r=1.0, g=1.0, b=1.0, a=1.0)
            t.text = label
            arr.markers.append(t)

        part = mk(2, Marker.CUBE,
                  'tool0_tcp' if self.part_attached else 'world')
        if self.part_attached:
            part.pose.position = Point(x=0.0, y=0.0, z=0.0)
        else:
            part.pose.position = Point(x=self.part_pos[0], y=self.part_pos[1],
                                       z=self.part_pos[2])
        part.scale.x = part.scale.y = part.scale.z = size
        part.color = ColorRGBA(r=0.95, g=0.55, b=0.05,
                               a=1.0 if self.part_visible else 0.0)
        arr.markers.append(part)

        st = mk(3, Marker.TEXT_VIEW_FACING)
        st.pose.position = Point(x=0.0, y=0.0, z=0.95)
        st.scale.z = 0.04
        st.color = ColorRGBA(r=1.0, g=0.9, b=0.2, a=1.0)
        # RViz2 separa visualmente las palabras de un TEXT_VIEW_FACING;
        # se muestra solo el estado de I/O (sin espacios).
        st.text = self.io_text.replace(' ', '|')
        arr.markers.append(st)
        self.marker_pub.publish(arr)


def main():
    rclpy.init()
    node = PickPlaceNode()
    ex = MultiThreadedExecutor(num_threads=4)
    ex.add_node(node)
    th = threading.Thread(target=ex.spin, daemon=True)
    th.start()
    try:
        node.run()
        time.sleep(1.0)
    except (KeyboardInterrupt, TimeoutError, RuntimeError) as e:
        node.get_logger().error(f'Rutina detenida: {e}')
    finally:
        ex.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
