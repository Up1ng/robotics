# ПР04 — параметры движения

Продолжение ПР03: `patrol` хранит последнюю позу и публикует Twist по таймеру.
`linear_speed=0.5` (0–1 м/с), `turn_rate=0.3` (−1–1 рад/с),
`publish_hz=10.0` (1–30 Гц). Принимаются только конечные числа.
До первой позы команда нулевая. Имена `pose` и `cmd_vel` относительные.

В Docker с ROS 2 Jazzy и пакетами turtlesim, pytest, ament:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
python3 -m pytest src/patrol/test
colcon test --event-handlers console_direct+
colcon test-result --verbose
```

В отдельных терминалах с тем же окружением и ROS_DOMAIN_ID:

```bash
ros2 run turtlesim turtlesim_node
ros2 run patrol patrol --ros-args -r pose:=/turtle1/pose -r cmd_vel:=/turtle1/cmd_vel
ros2 param set /patrol publish_hz 5.0
ros2 param set /patrol publish_hz 0.0
ros2 param get /patrol publish_hz
```

Последний set отклоняется, get возвращает 5.0. `on_set` только проверяет
кандидат; `post_set` применяет принятый пакет. Поэтому отклонение всего
пакета параметров не меняет скорость, частоту или таймер. При смене частоты
старый таймер отменяется и удаляется. SingleThreadedExecutor исключает
одновременное выполнение callback двух таймеров во время замены.

Полный живой опыт: `python3 scripts/pr04_demo.py`. Для среды без экрана
можно задать `QT_QPA_PLATFORM=offscreen`: turtlesim и ROS-граф остаются реальными,
проверяется поток команд; видимое окно этим способом не проверяется.

Course kit v1-w06 закреплён в `.github/ci/course-kit-v1-w06.tar.gz`, SHA-256:
`6eda53e1c566f7f0a7e09d7afe1e5a6f3b98397175a7e57dede9a84c6d14d0fe`.

```bash
mkdir -p .course-kit
tar -xzf .github/ci/course-kit-v1-w06.tar.gz -C .course-kit
python3 .course-kit/v1/tools/check_practice.py PR04 --submission .
```

Задание: https://ros.lms.ci.nsu.ru/practices/pr04 .
Результаты и команды — `evidence/pr04/parameters.md`.
