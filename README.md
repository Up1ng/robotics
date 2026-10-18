# ПР06 — модель Ackermann, tf2 и durability

Пакет `course_description` содержит URDF/Xacro, launch и конфигурацию RViz.
Размеры взяты из `models/course_ackermann/model.sdf` course-kit v1-w06:
база колёс 0.8 м, колея 0.62 м, радиус 0.12 м, ширина колеса 0.07 м,
корпус 1.05 × 0.52 × 0.22 м. SDF используется как источник размеров;
плагины Gazebo в URDF не переносятся.

Оси REP-103: X вперёд, Y влево, Z вверх. `base_link` находится на уровне
осей колёс. Геометрия корпуса смещена вверх на 0.12 м. Камера, лидар и IMU
имеют offset (0.28, 0, 0.38) относительно base_link, как в исходной SDF.
Их совпадающие позиции намеренно сохранены. Дополнительный
`camera_optical_frame` использует Z вперёд, X вправо, Y вниз.

У физических звеньев раздельные visual/collision и конечные положительные
массы и тензоры инерции. Формулы инерции бокса и цилиндра соответствуют
использованным простым формам; формы корпусов сенсоров иллюстративные,
поскольку исходная SDF не задаёт их visual/collision.

## Docker и проверки

```bash
docker build -t robotics-pr06 .
docker run --rm -it -e ROS_DOMAIN_ID=66 \
  -v "$PWD:/workspace" -w /workspace robotics-pr06 bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
xacro src/course_description/urdf/vehicle.urdf.xacro > /tmp/vehicle.urdf
check_urdf /tmp/vehicle.urdf
python3 -m pytest src/course_description/test
colcon test --packages-select course_description --event-handlers console_direct+
colcon test-result --verbose
```

ROS Jazzy остаётся внутри Docker. Для проверки course-kit распаковать
закреплённый архив и выполнить checker после подготовки evidence:

```bash
mkdir -p .course-kit
tar -xzf .github/ci/course-kit-v1-w06.tar.gz -C .course-kit
python3 .course-kit/v1/tools/check_practice.py PR06 --submission .
```

SHA-256 комплекта:
`6eda53e1c566f7f0a7e09d7afe1e5a6f3b98397175a7e57dede9a84c6d14d0fe`.
Для checker в Git worktree смонтировать также общий .git по его исходному
абсолютному пути: `git rev-parse --path-format=absolute --git-common-dir`.
При запуске root в контейнере: `git config --global --add safe.directory /workspace`.

## Модель и RViz

В контейнере без внешнего X11-дисплея запустить Xvfb:

```bash
Xvfb :99 -screen 0 1280x900x24 -nolisten tcp &
ros2 launch course_description display.launch.py
```

Dockerfile задаёт DISPLAY=:99, QT_QPA_PLATFORM=xcb и программный OpenGL.
Это настоящий RViz на виртуальном дисплее. Снимок окна можно сохранить
командой `import -window root /workspace/rviz.png`.
Для видимого окна на Linux передать контейнеру свой DISPLAY и X11-сокет,
предварительно разрешив доступ только нужному пользователю; Xvfb тогда не нужен.

Fixed Frame в готовой конфигурации — base_link. map/odom пока никто не публикует.
Вариант без RViz: `ros2 launch course_description display.launch.py rviz:=false`.
Изменение геометрии:

```bash
ros2 launch course_description display.launch.py \
  wheelbase:=1.0 track:=0.7 wheel_radius:=0.15
```

robot_state_publisher сразу публикует фиксированные сенсоры в /tf_static.
Для колёс и рулевых сочленений нужны joint_states. В отдельном терминале
контейнера с обоими setup.bash и тем же ROS_DOMAIN_ID:

```bash
ros2 topic pub -r 10 /joint_states sensor_msgs/msg/JointState \
  '{header: auto, name: [front_left_steering_joint, front_right_steering_joint, front_left_wheel_joint, front_right_wheel_joint, rear_left_wheel_joint, rear_right_wheel_joint], position: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}'
```

Это готовый CLI-издатель положений, а не дополнительный владелец tf.
Единственный владелец преобразований модели — robot_state_publisher.

## QoS и отказ

После запуска модели сравнить поздних подписчиков, задавая QoS явно:

```bash
ros2 topic info /tf_static --verbose --no-daemon --spin-time 3
timeout 4s ros2 topic echo /tf_static --once \
  --qos-durability transient_local --qos-reliability reliable
timeout 4s ros2 topic echo /tf_static --once \
  --qos-durability volatile --qos-reliability reliable
ros2 run tf2_ros tf2_echo base_link lidar_link
ros2 run tf2_tools view_frames
```

Transient local получает сохранённые преобразования, volatile ждёт новых
и завершается по timeout (124). Это отличается от несовместимой reliability
в ПР05: volatile совместим, но не запрашивает историческое сообщение.

Намеренный дефект меняет только parent lidar_joint с base_link на camera_link
при неизменном offset. Дерево остаётся структурно допустимым, но позиция
лидара относительно base_link удваивается: (0.56, 0, 0.76) вместо (0.28, 0, 0.38).
Тест test_lidar_parent обнаруживает эту ошибку, даже когда check_urdf успешен.

Полный опыт: смонтировать worktree ветки pr06-defect в /defect только для чтения
и выполнить `python3 scripts/pr06_demo.py` с подключённым окружением.
Сценарий сам запускает и останавливает свой Xvfb, joint_states, launch и RViz;
сохраняет тест до/после, реальные tf2_echo, view_frames, QoS и снимки окон в
`evidence/pr06/`. Не запускать другие экземпляры в том же домене во время опыта.

Задание: https://ros.lms.ci.nsu.ru/practices/pr06 .
