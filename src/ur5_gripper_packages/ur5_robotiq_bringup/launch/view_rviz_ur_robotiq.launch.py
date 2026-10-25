from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    ur_type = LaunchConfiguration("ur_type")
    tf_prefix = LaunchConfiguration("tf_prefix")

    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name="xacro")]), " ",
        PathJoinSubstitution([
            FindPackageShare("ur5_robotiq_description"),
            "urdf",
            "ur_with_gripper_sim.urdf.xacro"
        ]),
        " ",
        "name:=ur",
        " ",
        "ur_type:=", ur_type,
        " ",
        "tf_prefix:=", tf_prefix,
        " ",
        "parent_link:=world",
    ])

    robot_description = {
        "robot_description": ParameterValue(
            robot_description_content,
            value_type=str
        )
    }

    # Joint state publisher (for non-fixed joints)
    jsp = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        parameters=[{"use_sim_time": False}],
        output="both",
    )

    # Robot state publisher
    rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"use_sim_time": False}, robot_description],
        output="both",
    )

    # RViz
    rviz_config = PathJoinSubstitution([
        FindPackageShare("ur5_robotiq_bringup"),
        "rviz",
        "view_robot_ur_robotiq.rviz"
    ])

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_config],
        output="screen",
    )

    return LaunchDescription([
        DeclareLaunchArgument("ur_type", default_value="ur5"),
        DeclareLaunchArgument("tf_prefix", default_value=""),
        jsp,
        rsp,
        rviz,
    ])