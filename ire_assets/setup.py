from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'ire_assets'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'worlds'),
            glob(os.path.join('worlds', '*.world'))),
        (os.path.join('share', package_name, 'models', 'red_pillar'),
            glob(os.path.join('models', 'red_pillar', 'model.*'))),
        (os.path.join('share', package_name, 'models', 'aruco_box'),
            glob(os.path.join('models', 'aruco_box', 'model.*'))),
        (os.path.join('share', package_name, 'models', 'aruco_box', 'materials', 'scripts'),
            glob(os.path.join('models', 'aruco_box', 'materials', 'scripts', '*'))),
        (os.path.join('share', package_name, 'models', 'aruco_box', 'materials', 'textures'),
            glob(os.path.join('models', 'aruco_box', 'materials', 'textures', '*'))),
        (os.path.join('share', package_name, 'rviz'),
            glob(os.path.join('rviz', '*.rviz'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Jinseong Park',
    maintainer_email='js.park@cnu.ac.kr',
    description='지능로봇실습(IRE) 강의 패키지',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            
        ],
    },
)
