# ire_assets

주차별 실습에 쓰는 Gazebo 자원을 모아둔 공용 패키지입니다. 실행 노드는 없습니다.

| 경로 | 내용 | 사용 주차 |
|---|---|---|
| `models/red_pillar/` | 빨간 기둥 (색 검출 대상) | 8 |
| `models/aruco_box/` | ArUco 마커(id 0) 박스 | 8, 11 |
| `worlds/ire_maze.world` | 미로 월드 (출발 `(-2.0, 2.0)` → 도착 `(2.0, -2.0)`) | 미션 |
| `rviz/` | 주차별 RViz 설정(`.rviz`) 보관 위치 | — |

다른 패키지의 launch에서 `get_package_share_directory('ire_assets')`로 경로를 얻어
`spawn_entity.py`에 넘기는 방식으로 사용합니다.

```python
pillar_sdf = os.path.join(get_package_share_directory('ire_assets'),
                          'models', 'red_pillar', 'model.sdf')
```

## 미로 월드 사용

```bash
ros2 launch turtlebot3_manipulation_gazebo gazebo.launch.py \
  world:=$(ros2 pkg prefix ire_assets)/share/ire_assets/worlds/ire_maze.world \
  x_pose:=-2.0 y_pose:=2.0
```

## 모델을 추가하려면

Gazebo 모델은 **디렉터리 한 개 = 모델 한 개**이며 파일 두 개가 필요합니다.

```
models/<모델이름>/
├── model.config     ← 모델 이름·설명 (Gazebo가 목록에 표시할 때 읽음)
└── model.sdf        ← 형상·재질·물리 속성
```

`model.config`의 `<name>`과 디렉터리 이름을 같게 맞추십시오.

**★ `setup.py`의 `data_files`에 등록해야 설치됩니다.** 등록하지 않으면 빌드는 성공하는데
`spawn_entity.py`가 파일을 찾지 못합니다.

```python
(os.path.join('share', package_name, 'models', '<모델이름>'),
    glob(os.path.join('models', '<모델이름>', 'model.*'))),
```

등록 후 빌드하고 확인합니다.

```bash
cd ~/ire_ws && colcon build --symlink-install --packages-select ire_assets
ls $(ros2 pkg prefix ire_assets)/share/ire_assets/models/
```

### 색만 바꾸는 경우 — SDF에 직접 지정

`red_pillar`처럼 단색이면 `model.sdf` 안에서 끝납니다. 추가 파일이 없어 가장 간단합니다.

```xml
<material>
  <ambient>0.8 0.05 0.05 1</ambient>
  <diffuse>0.9 0.05 0.05 1</diffuse>
</material>
```

### 이미지를 붙이는 경우 — 텍스처

`aruco_box`처럼 표면에 그림을 붙이려면 파일이 더 필요하고, 아래 세 가지를 모두
만족해야 화면에 나타납니다. 하나라도 빠지면 **민무늬 회색 상자**로 렌더링됩니다.

```
models/aruco_box/
├── model.sdf
├── model.config
└── materials/
    ├── scripts/aruco_box.material   ← 머티리얼 정의 (texture 파일명 지정)
    └── textures/aruco_0.png         ← 실제 이미지
```

1. `model.sdf`가 `<uri>model://<모델이름>/materials/...</uri>`로 경로를 참조할 것
2. `setup.py`에 `materials/scripts`, `materials/textures`가 모두 등록될 것
3. **`package.xml`에 Gazebo 모델 경로 export가 있을 것** — 이것이 없으면 `model://`
   URI 자체가 해석되지 않습니다.

```xml
<export>
  <build_type>ament_python</build_type>
  <gazebo_ros gazebo_model_path="${prefix}/models"/>
</export>
```

> ArUco 마커를 텍스처로 쓸 때는 **마커 둘레에 흰 여백**을 남기십시오.
> 여백이 없으면 검출되지 않습니다. `ros2 run ire_week08_vision generate_aruco`가
> 여백을 포함해 생성합니다.
