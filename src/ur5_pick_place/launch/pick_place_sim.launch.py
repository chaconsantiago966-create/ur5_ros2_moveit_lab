"""Simulación completa de la rutina Pick & Place.

Lanza:
  1. Gazebo + UR5 con gripper (launch del paquete ur5_robotiq_bringup)
     usando el mundo de la celda (estaciones PICK y PLACE).
  2. Simulador de entradas/salidas digitales (digital_io_sim).
  3. RViz con modelo del robot, marcadores de la celda y estado de I/O.
  4. Nodo pick_place_node (tras un retardo para que los controladores
     estén activos).

Uso:
  ros2 launch ur5_pick_place pick_place_sim.launch.py
  ros2 launch ur5_pick_place pick_place_sim.launch.py gazebo_gui:=false
  ros2 launch ur5_pick_place pick_place_sim.launch.py auto_cell:=false
"""
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            TimerAction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare('ur5_pick_place')
    gazebo_gui = LaunchConfiguration('gazebo_gui')
    auto_cell = LaunchConfiguration('auto_cell')
    start_routine = LaunchConfiguration('start_routine')
    rviz = LaunchConfiguration('rviz')

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('ur5_robotiq_bringup'), 'launch',
             'sim_gz_sgb.launch.py'])),
        launch_arguments={
            'gazebo_gui': gazebo_gui,
            'launch_rviz': 'false',
            'world_file': PathJoinSubstitution(
                [pkg, 'worlds', 'pick_place_cell.sdf']),
        }.items())

    io = Node(package='ur5_pick_place', executable='digital_io_sim',
              output='screen',
              parameters=[PathJoinSubstitution([pkg, 'config',
                                                'digital_io.yaml']),
                          {'auto_cell': auto_cell, 'use_sim_time': True}])

    rviz_node = Node(package='rviz2', executable='rviz2', output='log',
                     arguments=['-d', PathJoinSubstitution(
                         [pkg, 'rviz', 'pick_place.rviz'])],
                     parameters=[{'use_sim_time': True}],
                     condition=IfCondition(rviz))

    routine = Node(package='ur5_pick_place', executable='pick_place_node',
                   output='screen',
                   parameters=[PathJoinSubstitution(
                       [pkg, 'config', 'pick_place_routine.yaml'])],
                   condition=IfCondition(start_routine))

    return LaunchDescription([
        DeclareLaunchArgument('gazebo_gui', default_value='true'),
        DeclareLaunchArgument('auto_cell', default_value='true',
                              description='Lógica de celda automática'),
        DeclareLaunchArgument('start_routine', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        sim, io, rviz_node,
        TimerAction(period=15.0, actions=[routine]),
    ])
