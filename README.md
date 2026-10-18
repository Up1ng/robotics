# ПР05 — launch, QoS и повтор MCAP

Продолжение ПР04. Один глобальный turtlesim, а `patrol`, `pose_relay` и
`pose_subscriber` работают в `/robot_a`. Ноды используют относительные имена;
launch переназначает `pose` в `/turtle1/pose`, команду — в `/turtle1/cmd_vel`.
Relay публикует `/robot_a/sensor_pose` с best_effort. Надёжность отдельного
подписчика выбирается при запуске.

## Docker и сборка

```bash
docker build -t robotics-labs .
docker run --rm -it -e ROS_DOMAIN_ID=56 \
  -v "$PWD:/workspace" -w /workspace robotics-labs bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
colcon test --event-handlers console_direct+
colcon test-result --verbose
```

Dockerfile закрепляет digest ROS Jazzy; работает на arm64 и amd64. По умолчанию
Qt работает offscreen: это реальный turtlesim без видимого окна.
На Linux для видимого окна передайте DISPLAY и X11-сокет и переопределите
`QT_QPA_PLATFORM=xcb`, разрешив контейнеру доступ к своему дисплею.

## Живой опыт

Из нового терминала внутри контейнера подключить оба setup.bash.

```bash
ros2 launch course_bringup patrol.launch.py \
  namespace:=robot_a subscriber_reliability:=reliable record:=false
# В другом терминале того же контейнера:
ros2 topic info /robot_a/sensor_pose --verbose
timeout 5s ros2 topic echo /robot_a/sensor_pose --qos-reliability reliable --once
```

Timeout ожидаем: best_effort-издатель не удовлетворяет reliable-подписчику.
Остановить launch и повторить с совместимым профилем и записью:

```bash
ros2 launch course_bringup patrol.launch.py namespace:=robot_a \
  subscriber_reliability:=best_effort record:=true bag_dir:=evidence/pr05/bag
timeout 5s ros2 topic echo /robot_a/sensor_pose --qos-reliability best_effort --once
```

`record` обрабатывается через IfCondition, при false recorder отсутствует.
`bag_dir` должен ещё не существовать. После нескольких секунд остановить launch
через Ctrl+C и дождаться сохранения metadata.yaml.

## Повтор той же записи

Живой launch должен быть остановлен. Используется ровно один записанный топик:

```bash
ros2 bag info evidence/pr05/bag
ros2 bag play evidence/pr05/bag --loop \
  --qos-profile-overrides-path config/qos-overrides.yaml
# В другом терминале:
timeout 5s ros2 topic echo /robot_a/sensor_pose --qos-reliability reliable --once
timeout 5s ros2 topic echo /robot_a/sensor_pose --qos-reliability best_effort --once
```

Первый подписчик не получает сообщений, второй получает. Override сохраняет
best_effort у player, поэтому проверяется та же несовместимость, что и вживую.
Конфигурация также установлена в share/course_bringup/config.
Для другого namespace нужно соответствующим образом изменить ключ в override.

Полное воспроизведение: `python3 scripts/pr05_demo.py` в контейнере с подключёнными
setup.bash. Скрипт не перезаписывает существующий bag; перед новым опытом перенесите
его в другое место. Логи, запись и метаданные — в `evidence/pr05/`.

Course kit v1-w06: `.github/ci/course-kit-v1-w06.tar.gz`, SHA-256
`6eda53e1c566f7f0a7e09d7afe1e5a6f3b98397175a7e57dede9a84c6d14d0fe`.

```bash
mkdir -p .course-kit
tar -xzf .github/ci/course-kit-v1-w06.tar.gz -C .course-kit
python3 .course-kit/v1/tools/check_practice.py PR05 --submission .
```

Задание: https://ros.lms.ci.nsu.ru/practices/pr05 .
