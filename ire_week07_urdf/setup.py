from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'ire_week07_urdf'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*.launch.py'))),
        (os.path.join('share', package_name, 'urdf'),
            glob(os.path.join('urdf', '*.urdf'))),
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
