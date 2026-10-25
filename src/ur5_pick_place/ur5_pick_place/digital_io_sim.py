#!/usr/bin/env python3
"""Simulador de entradas/salidas digitales (I/O) de la celda robotizada.

Emula el módulo de I/O de un controlador de robot (o un PLC) usando
tópicos y servicios estándar de ROS 2, sin mensajes personalizados.

Interfaz
--------
Entradas digitales (DI) -> sensores de la celda
  * Tópico  /io/di<n>          std_msgs/Bool   (estado, QoS transient_local)
  * Servicio /io/di<n>/set     std_srvs/SetBool (forzar el estado desde
                                                  terminal, HMI o pruebas)
Salidas digitales (DO) -> actuadores de la celda
  * Tópico  /io/do<n>          std_msgs/Bool   (estado, QoS transient_local)
  * Servicio /io/do<n>/set     std_srvs/SetBool (el robot activa la salida)
Resumen legible
  * Tópico  /io/state           std_msgs/String  (p. ej. "DI=0100 DO=1000")

Lógica de celda simulada (parámetro auto_cell=True)
  * DO0 (banda transportadora) = ON  -> tras `part_arrival_delay` s se
    activa DI0 (pieza presente en el punto de recogida).
  * DO1 (señal "pieza depositada") = ON -> se activa DI1 (zona de descarga
    libre / confirmación del PLC) tras `ack_delay` s.
  DI2 (zona de descarga libre) arranca en ON (parámetro initial_inputs_on).
  Con auto_cell=False las entradas solo cambian por servicio, de modo que el
  operador las controla manualmente con `ros2 service call`.
"""
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from std_msgs.msg import Bool, String
from std_srvs.srv import SetBool


class DigitalIOSim(Node):

    def __init__(self):
        super().__init__('digital_io_sim')
        self.declare_parameter('num_inputs', 4)
        self.declare_parameter('num_outputs', 4)
        self.declare_parameter('auto_cell', True)
        self.declare_parameter('part_arrival_delay', 2.0)
        self.declare_parameter('ack_delay', 1.5)
        # Entradas que arrancan en ON (p. ej. DI2 = zona de descarga libre)
        self.declare_parameter('initial_inputs_on', [2])

        self.n_di = self.get_parameter('num_inputs').value
        self.n_do = self.get_parameter('num_outputs').value
        self.auto = self.get_parameter('auto_cell').value

        self.di = [False] * self.n_di
        for i in self.get_parameter('initial_inputs_on').value:
            if 0 <= i < self.n_di:
                self.di[i] = True
        self.do = [False] * self.n_do

        qos = QoSProfile(depth=1,
                         durability=DurabilityPolicy.TRANSIENT_LOCAL,
                         reliability=ReliabilityPolicy.RELIABLE)
        self.di_pub = [self.create_publisher(Bool, f'/io/di{i}', qos)
                       for i in range(self.n_di)]
        self.do_pub = [self.create_publisher(Bool, f'/io/do{i}', qos)
                       for i in range(self.n_do)]
        self.state_pub = self.create_publisher(String, '/io/state', qos)

        self._srv = []
        for i in range(self.n_di):
            self._srv.append(self.create_service(
                SetBool, f'/io/di{i}/set',
                lambda req, res, i=i: self._set('di', i, req, res)))
        for i in range(self.n_do):
            self._srv.append(self.create_service(
                SetBool, f'/io/do{i}/set',
                lambda req, res, i=i: self._set('do', i, req, res)))

        self._timers = []
        self._publish_all()
        self.get_logger().info(
            f'I/O simulado listo: {self.n_di} DI, {self.n_do} DO '
            f'(auto_cell={self.auto})')

    # ------------------------------------------------------------------
    def _set(self, kind, idx, req, res):
        self._write(kind, idx, bool(req.data))
        res.success = True
        res.message = f'{kind.upper()}{idx} = {"ON" if req.data else "OFF"}'
        if kind == 'do' and self.auto:
            self._cell_logic(idx, bool(req.data))
        return res

    def _write(self, kind, idx, value):
        arr = self.di if kind == 'di' else self.do
        if arr[idx] != value:
            self.get_logger().info(
                f'{kind.upper()}{idx}: {"OFF->ON" if value else "ON->OFF"}')
        arr[idx] = value
        self._publish_all()

    def _publish_all(self):
        for i, v in enumerate(self.di):
            self.di_pub[i].publish(Bool(data=v))
        for i, v in enumerate(self.do):
            self.do_pub[i].publish(Bool(data=v))
        s = 'DI=' + ''.join('1' if v else '0' for v in self.di) + \
            ' DO=' + ''.join('1' if v else '0' for v in self.do)
        self.state_pub.publish(String(data=s))

    def _later(self, delay, fn):
        """Ejecuta fn una sola vez tras `delay` segundos."""
        holder = {}

        def cb():
            holder['t'].cancel()
            self._timers.remove(holder['t'])
            fn()
        holder['t'] = self.create_timer(delay, cb)
        self._timers.append(holder['t'])

    def _cell_logic(self, do_idx, value):
        if do_idx == 0:
            if value:   # banda encendida -> llega una pieza
                d = self.get_parameter('part_arrival_delay').value
                self._later(d, lambda: self._write('di', 0, True))
            else:
                pass
        elif do_idx == 1:
            if value:   # pieza depositada -> PLC confirma y retira pieza
                d = self.get_parameter('ack_delay').value

                def ack():
                    self._write('di', 1, True)
                    self._write('di', 0, False)
                self._later(d, ack)
            else:
                self._write('di', 1, False)


def main():
    rclpy.init()
    node = DigitalIOSim()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
