from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'ire_week10_nav_demo'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Jinseong Park',
    maintainer_email='js.park@cnu.ac.kr',
    description='지능로봇실습(IRE) 강의 패키지',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'go_to_pose = ire_week10_nav_demo.go_to_pose:main'
        ],
    },
)
