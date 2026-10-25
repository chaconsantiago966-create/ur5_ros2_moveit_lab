from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'ur5_robotiq_bringup'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        # Ament resource index
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),

        # Install package.xml
        ('share/' + package_name, ['package.xml']),

        # Install launch files
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),

        # Install config files
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),

        # Install RViz configs
        (os.path.join('share', package_name, 'rviz'),
            glob('rviz/*.rviz')),

        # Install worlds (optional)
        (os.path.join('share', package_name, 'worlds'),
            glob('worlds/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Daniel Palomino',
    maintainer_email='daniel.palomino-s@escuelaing.edu.co',
    description='Bringup package for UR5 + Robotiq simulation in Gazebo (GZ)',
    license='TODO: License declaration',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            # No Python nodes yet, but ready for future labs
        ],
    },
)
