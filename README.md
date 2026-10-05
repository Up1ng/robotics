# ПР03 — первая нода: поза и команда

Продолжение ПР02: пакет `turtle_bringup` сохранён; новый пакет `patrol`
использует ROS 2 Jazzy, `rclpy`, `geometry_msgs` и `turtlesim/msg/Pose`.
Подписка хранит последнюю позу, таймер каждые 0,1 с публикует Twist.
До первой позы команда нулевая, после — `linear.x=0.5`, `angular.z=0.3`.
Чистая функция `command_for_pose` проверяется без запуска ROS-графа.

## Docker

Проверенный образ:
`osrf/ros:jazzy-desktop-full@sha256:ae7ad3ac243da1dfd8bd402a2fa08e149ffbf7a385013bd8ef798d0800accdc8`.
Запускать из корня репозитория, с работающим X11-дисплеем:

```bash
xhost +si:localuser:root
sudo docker run --rm -it --name robotics-pr03 \
  --network host --ipc host \
  -e DISPLAY="$DISPLAY" -e ROS_DOMAIN_ID=36 -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$PWD:/workspace" -w /workspace \
  osrf/ros:jazzy-desktop-full@sha256:ae7ad3ac243da1dfd8bd402a2fa08e149ffbf7a385013bd8ef798d0800accdc8 bash
```

В контейнере:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
python3 -m pytest src/patrol/test
colcon test --event-handlers console_direct+
colcon test-result --verbose
```

В каждой дополнительной оболочке подключить оба `setup.bash`; домен должен
совпадать. Для дополнительного терминала: `sudo docker exec -it robotics-pr03 bash`.

Терминал 1:

```bash
ros2 launch turtle_bringup sim.launch.py
```

Терминал 2 — дефект:

```bash
ros2 run patrol patrol
```

Поза поступает, но относительное `cmd_vel` становится `/cmd_vel`, а turtlesim
подписан на `/turtle1/cmd_vel`. Остановить patrol через Ctrl+C, затем исправить:

```bash
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

Терминал 3:

```bash
ros2 node info /patrol
ros2 topic type /turtle1/pose
ros2 topic info /turtle1/cmd_vel --verbose
ros2 topic hz /turtle1/cmd_vel --window 100
```

Измерять 10 секунд. После Ctrl+C у patrol дождаться нулевых скоростей
в `/turtle1/pose`: turtlesim останавливает черепаху по своему таймауту команд.
Затем остановить launch. После завершения Docker отозвать X11-доступ:
`xhost -si:localuser:root`.

## Воспроизведение опыта и проверка сдачи

`python3 scripts/pr03_demo.py` внутри контейнера с подключённым окружением
сам запускает и останавливает свои процессы. Перед повтором остановить другие
экземпляры turtlesim/patrol в домене 36. Скрипт проверяет нулевые команды без
позы, 10 секунд дефекта, 10 секунд после remap, частоту и остановку;
перезаписывает соответствующие логи в `evidence/pr03/`.

Зафиксированный course-kit: `v1-w05`, SHA-256
`bca214e3de6f90f9513049dfa0f36fee65ad834da502dc3f3f8fb443517b5197`.

```bash
mkdir -p .course-kit
curl -fsSLo /tmp/pr03-kit.tar.gz \
  https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1-w05-bca214e3de6f.tar.gz
printf '%s  %s\n' \
  bca214e3de6f90f9513049dfa0f36fee65ad834da502dc3f3f8fb443517b5197 \
  /tmp/pr03-kit.tar.gz | sha256sum -c -
tar -xzf /tmp/pr03-kit.tar.gz -C .course-kit
python3 .course-kit/v1/tools/check_practice.py PR03 --submission .
```

Результаты и объяснения — в `evidence/pr03/demo.md`; CI —
`.github/workflows/pr03.yml`. Отчёт ссылается на коммит реализации,
а сдаётся последующий коммит с evidence. Необязательный маршрут мышью не входит
в эту работу.
