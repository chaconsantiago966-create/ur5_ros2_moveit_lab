import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'ur5_pick_place'

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
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.sdf')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Santiago Chacón',
    maintainer_email='chaconsantiago966@users.noreply.github.com',
    description='Rutina Pick and Place simulada para UR5 + gripper',
    license='MIT',
    entry_points={
        'console_scripts': [
            'pick_place_node = ur5_pick_place.pick_place_node:main',
            'digital_io_sim = ur5_pick_place.digital_io_sim:main',
        ],
    },
)
