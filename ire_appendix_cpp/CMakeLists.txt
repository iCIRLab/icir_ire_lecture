# CMakeLists.txt : ament_cmake 패키지의 "빌드 설명서" (3주차 Appendix B2 슬라이드의 실물)
# setup.py가 하던 일을 이 파일이 합니다 — 노드 등록은 add_executable + install(TARGETS).
cmake_minimum_required(VERSION 3.8)         # CMake 최소 버전 — 그대로
project(ire_appendix_cpp)                   # 패키지 이름 — package.xml과 일치

find_package(ament_cmake REQUIRED)          # 빌드 도구
find_package(rclcpp REQUIRED)               # 의존 패키지 — 쓰는 만큼 반복
find_package(std_msgs REQUIRED)

add_executable(practice src/practice.cpp)   # ★ 실행파일 이름 ← 소스 연결
ament_target_dependencies(practice rclcpp std_msgs)   # 실행파일에 의존성 연결

install(TARGETS practice                    # ★ install/로 복사 — 이걸 해야
  DESTINATION lib/${PROJECT_NAME})          #   ros2 run이 찾는다 (3주차 5쪽)

# 파이썬 스크립트를 섞을 때 (혼합 언어 패키지):
# install(PROGRAMS scripts/helper.py DESTINATION lib/${PROJECT_NAME})

# 커스텀 msg·srv를 만들 때 (4주차 26쪽):
# find_package(rosidl_default_generators REQUIRED)
# rosidl_generate_interfaces(${PROJECT_NAME} "srv/MyCmd.srv")

ament_package()                             # 마지막 줄 고정 — 패키지 등록 마무리
