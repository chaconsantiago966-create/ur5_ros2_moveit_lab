"""Gazebo + MoveIt (move_group) + RViz (plugin MoveIt) + nodo moveit_executor.

Usa el paquete generado con el MoveIt Setup Assistant
(ur5_robotiq_moveit_config) contra el robot simulado en Gazebo del
repositorio base (ur5_robotiq_bringup).

  ros2 launch ur5_moveit_executor moveit_gazebo.launch.py
  ros2 launch ur5_moveit_executor moveit_gazebo.launch.py run_executor:=false
"""
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            TimerAction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder
import os


def generate_launch_description():
    here = get_package_share_directory('ur5_moveit_executor')
    moveit_config = (
        MoveItConfigsBuilder('ur', package_name='ur5_robotiq_moveit_config')
        .trajectory_execution(file_path=os.path.join(
            here, 'config', 'moveit_controllers_gazebo.yaml'))
        .planning_pipelines(pipelines=['ompl', 'pilz_industrial_motion_planner'])
        .moveit_cpp(file_path=os.path.join(here, 'config', 'moveit_py.yaml'))
        .to_moveit_configs())
    sim_time = {'use_sim_time': True}

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('ur5_robotiq_bringup'), 'launch',
             'sim_gz_sgb.launch.py'])),
        launch_arguments={
            'gazebo_gui': LaunchConfiguration('gazebo_gui'),
            'launch_rviz': 'false',
            'world_file': PathJoinSubstitution(
                [FindPackageShare('ur5_pick_place'), 'worlds',
                 'pick_place_cell.sdf']),
        }.items())

    move_group = Node(
        package='moveit_ros_move_group', executable='move_group',
        output='screen',
        parameters=[moveit_config.to_dict(), sim_time])

    rviz = Node(
        package='rviz2', executable='rviz2', output='log',
        arguments=['-d', os.path.join(here, 'rviz', 'moveit_executor.rviz')],
        parameters=[moveit_config.robot_description,
                    moveit_config.robot_description_semantic,
                    moveit_config.robot_description_kinematics,
                    moveit_config.planning_pipelines,
                    moveit_config.joint_limits, sim_time])

    executor = Node(
        package='ur5_moveit_executor', executable='moveit_executor',
        name='moveit_py', output='screen',
        parameters=[moveit_config.to_dict(), sim_time],
        condition=IfCondition(LaunchConfiguration('run_executor')))

    return LaunchDescription([
        DeclareLaunchArgument('gazebo_gui', default_value='true'),
        DeclareLaunchArgument('run_executor', default_value='true'),
        gazebo,
        TimerAction(period=12.0, actions=[move_group, rviz]),
        TimerAction(period=30.0, actions=[executor]),
    ])
