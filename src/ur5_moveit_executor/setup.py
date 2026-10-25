import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'ur5_moveit_executor'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Santiago Chacón',
    maintainer_email='chaconsantiago966@gmail.com',
    description='Ejecución de trayectorias con MoveItPy sobre UR5 en Gazebo',
    license='MIT',
    entry_points={'console_scripts': [
        'moveit_executor = ur5_moveit_executor.moveit_executor:main',
    ]},
)
