# ПР02 — пакет и запуск turtlesim

Пакет `turtle_bringup` создан командой `ros2 pkg create --build-type ament_python --license Apache-2.0 turtle_bringup --dependencies launch launch_ros turtlesim`. В нём нет собственной ноды: `sim.launch.py` запускает установленную `turtlesim_node`. Пакет и launch-файл проверены в Docker с ROS 2 Jazzy.

## Среда

- Образ: `osrf/ros:jazzy-desktop-full@sha256:ae7ad3ac243da1dfd8bd402a2fa08e149ffbf7a385013bd8ef798d0800accdc8`.
- Рабочий каталог репозитория монтируется в `/workspace`; `src/` и `evidence/` остаются на хосте.
- Для опыта использован `ROS_DOMAIN_ID=26`; в аудитории подставьте свой домен.

Запуск с графическим окном на Linux из корня репозитория:

```bash
xhost +si:localuser:root
sudo docker run -d --rm --name nsu-pr02 --network host --ipc host \
  -e DISPLAY="$DISPLAY" -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$PWD":/workspace -w /workspace \
  osrf/ros:jazzy-desktop-full@sha256:ae7ad3ac243da1dfd8bd402a2fa08e149ffbf7a385013bd8ef798d0800accdc8 \
  sleep infinity
sudo docker exec -it nsu-pr02 bash
```

В терминале контейнера:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=26
cd /workspace
colcon build --symlink-install --packages-select turtle_bringup
source install/setup.bash
ros2 pkg prefix turtle_bringup
ls "$(ros2 pkg prefix turtle_bringup)/share/turtle_bringup/launch"
ros2 launch turtle_bringup sim.launch.py
```

Откройте ещё один терминал того же контейнера, подключите `/opt/ros/jazzy/setup.bash` и `install/setup.bash`, установите тот же `ROS_DOMAIN_ID`. Проверьте граф и типы:

```bash
ros2 node list --no-daemon --spin-time 2
ros2 interface show geometry_msgs/msg/Twist
ros2 topic type /turtle1/pose
ros2 topic echo /turtle1/pose --once
```

Для движения отправьте команду:

```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
ros2 topic echo /turtle1/pose --once
```

Тот же `Twist` в `/cmd_vel` не двигает черепаху: у этого топика есть издатель, но нет подписчика. У `/turtle1/cmd_vel` есть подписчик `/turtlesim`. Для воспроизведения используйте непрерывную публикацию с `--wait-matching-subscriptions 0`, сравните `ros2 topic info /cmd_vel --verbose` и `ros2 topic info /turtle1/cmd_vel --verbose`, затем остановите издатель и повторите команду с правильным именем. Изменяйте только имя топика. Выводы и значения позы сохранены в [evidence/pr02/commands.md](evidence/pr02/commands.md) и сырых файлах рядом с ним.

Остановите launch через `Ctrl+C`: нода `/turtlesim` должна исчезнуть из графа. Затем на хосте выполните `sudo docker stop nsu-pr02` и `xhost -si:localuser:root`.

## Проверка сдачи

Архив course-kit `v1-w02` закреплён в `.github/ci/course-kit-v1-w02.tar.gz` (SHA-256 `5d210c431e32418f45e2cffa9dd2028116c7a9520a36f3c7079c778cd73437a8`). Он предоставлен курсом «Робототехника» НГУ, источник — `https://ros.lms.ci.nsu.ru/`; включён без изменений. Условия использования находятся в `v1/LICENSE.md` внутри архива.

CI проверяет архив, собирает пакет в том же Docker-образе, находит установленный `sim.launch.py` и запускает checker ПР02. Графический опыт выполнен локально и записан в evidence. Коммит реализации предшествует отдельному коммиту evidence; полный SHA реализации указан в `evidence/pr02/report.json`.
