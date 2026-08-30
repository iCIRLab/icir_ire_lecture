# setup.py — ament_python 패키지의 "빌드 설명서"
# ★ 표시가 붙은 곳만 여러분이 직접 만집니다. 나머지는 ros2 pkg create가 만들어준 그대로 두면 됩니다.
from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'ire_week03_pubsub'   # 패키지 이름 — 폴더·package.xml과 일치해야 함

setup(
    name=package_name,               # 패키지 이름
    version='0.1.0',                 # 버전 — package.xml과 맞춘다
    packages=find_packages(exclude=['test']),   # 파이썬 모듈 자동 탐색
    data_files=[                     # ★ 코드 외 파일을 install/로 복사하는 목록
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),      # 패키지 존재 알림용 빈 파일
        ('share/' + package_name, ['package.xml']),
        # ★ launch·urdf·yaml 파일은 여기 등록해야 설치된다. 예:
        # (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'], # pip 의존성 — 보통 그대로
    zip_safe=True,                   # 압축 설치 허용 — 신경 안 써도 됨
    maintainer='Jinseong Park',      # 관리자 정보 — 배포할 때만 중요
    maintainer_email='js.park@cnu.ac.kr',
    description='지능로봇실습(IRE) 강의 패키지',
    license='Apache-2.0',
    entry_points={                   # ★ ros2 run의 실행 이름표
        'console_scripts': [
            # '실행이름 = 파이썬모듈경로:함수' — ros2 run <패키지> <실행이름>
            'talker = ire_week03_pubsub.talker:main',
            'listener = ire_week03_pubsub.listener:main'
        ],
    },
)
