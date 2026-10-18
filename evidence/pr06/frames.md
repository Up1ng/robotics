# ПР06 — звенья, геометрия и владельцы tf

Опыт 2026-10-18: Docker, Ubuntu 24.04.5, ROS 2 Jazzy, arm64, Fast DDS,
ROS_DOMAIN_ID=66. Версии — environment.txt, локальный image ID — docker-image.txt,
закреплённый базовый digest — Dockerfile. Course-kit v1-w06, SHA-256
6eda53e1c566f7f0a7e09d7afe1e5a6f3b98397175a7e57dede9a84c6d14d0fe.

## Координаты и размеры

Единицы: метры, килограммы, секунды, радианы. Оси REP-103: X вперёд,
Y влево, Z вверх. База 0.8 м, колея 0.62 м, радиус колеса 0.12 м,
ширина 0.07 м. Корпус 1.05 × 0.52 × 0.22 м, центр на Z=0.12 м.
Геометрия и позиции заимствованы из исходной SDF, которая не изменялась.
SDF model pose (0, 0, 0.18) — положение спавна в мире Gazebo, а не новое
соединение URDF: world/map/odom в данной работе не публикуются.

Все три сенсора имеют одну исходную позицию (0.28, 0, 0.38) в SDF.
Она намеренно сохранена; размеры визуальных корпусов сенсоров иллюстративные,
поскольку SDF задаёт sensor, но не их visual/collision. Формы корпуса и колёс
имеют отдельные visual/collision, массы и допустимые тензоры инерции.

## Исправное дерево

11 звеньев, 10 сочленений, один корень base_link; связность и отсутствие циклов
проверены тестом, check_urdf и реальным view_frames. q обозначает соответствующее
положение из joint_states; в снимках все шесть q равны 0.

| Parent | Child | XYZ, м | RPY / движение, рад | Топик | Владелец |
|---|---|---|---|---|---|
| base_link | camera_link | 0.28, 0, 0.38 | 0, 0, 0 | /tf_static | robot_state_publisher |
| camera_link | camera_optical_frame | 0, 0, 0 | −π/2, 0, −π/2 | /tf_static | robot_state_publisher |
| base_link | lidar_link | 0.28, 0, 0.38 | 0, 0, 0 | /tf_static | robot_state_publisher |
| base_link | imu_link | 0.28, 0, 0.38 | 0, 0, 0 | /tf_static | robot_state_publisher |
| base_link | front_left_knuckle | 0.4, 0.31, 0 | вокруг Z, q ∈ [−0.55, 0.55] | /tf | robot_state_publisher |
| base_link | front_right_knuckle | 0.4, −0.31, 0 | вокруг Z, q ∈ [−0.55, 0.55] | /tf | robot_state_publisher |
| front_left_knuckle | front_left_wheel | 0, 0, 0 | вокруг Y, continuous q | /tf | robot_state_publisher |
| front_right_knuckle | front_right_wheel | 0, 0, 0 | вокруг Y, continuous q | /tf | robot_state_publisher |
| base_link | rear_left_wheel | −0.4, 0.31, 0 | вокруг Y, continuous q | /tf | robot_state_publisher |
| base_link | rear_right_wheel | −0.4, −0.31, 0 | вокруг Y, continuous q | /tf | robot_state_publisher |

У base_link нет родителя или внешнего владельца положения в мире.
Оптический фрейм использует Z вперёд, X вправо, Y вниз.

В tf-qos.txt у /tf_static и /tf ровно один publisher — robot_state_publisher.
Готовый ros2 topic pub даёт шесть joint_states с нулевыми положениями 10 Гц
для отображения всех колёс; он не публикует tf. joint_state_publisher не нужен.
Без joint_states фиксированные сенсоры всё равно доступны в /tf_static.
В view_frames `default_authority` — строка tf2-буфера, а владелец подтверждён
диагностикой ROS-топиков. Значение rate=10000 для статических связей — условность
view_frames при нулевом интервале, а не измеренная частота публикации.

## Намеренный дефект

Ветка pr06-defect, commit `489f80cef4881af976db23232ec20d8521793d61`.
Изменена ровно одна строка: parent lidar_joint стал camera_link вместо base_link.
Offset (0.28, 0, 0.38) оставлен прежним. Поэтому base→camera→lidar даёт
суммарные (0.56, 0, 0.76), что подтверждено живым tf2_echo в before-tf.txt.

check_urdf по-прежнему возвращает 0 (model-check.txt): дерево связное,
но смысл положения неверен. Тот же test_lidar_parent с PR06_XACRO,
указывающим на дефектный файл, возвращает 1 (defect-test.txt).
RViz отображает поднятый и смещённый оранжевый лидар (before-rviz.png).

## Исправление и QoS

В pr06 parent остаётся base_link. Тот же тест возвращает 0 (fixed-test.txt),
tf2_echo даёт (0.28, 0, 0.38) (after-tf.txt). Оба настоящих окна RViz открылись
в Xvfb, используют программный OpenGL 4.5 и показывают Global Status: Ok;
снимки before-rviz.png и after-rviz.png действительно просмотрены.
Fixed Frame=base_link. Графы до/после сохранены в before-frames/ и after-frames/.

При продолжающейся работе исправного robot_state_publisher поздний echo
с reliable+transient_local получает четыре фиксированных преобразования
и код 0. Echo с reliable+volatile ничего не получает и завершается с 124.
Это совместимые профили, но volatile не запрашивает историческое сообщение.
Всё сохранено в tf-qos.txt вместе с профилем динамического /tf и пояснением.
Во время сравнения publisher не перезапускался и URDF не обновлялся.

Предупреждение KDL о root inertia означает, что KDL не использует инерцию
корневого base_link. В этой работе RSP рассчитывает кинематику, динамика KDL
не рассчитывается; массы и тензоры сохраняются и проверяются в самом URDF.

## Проверки и повторение

В Docker подключены /opt/ros/jazzy/setup.bash и install/setup.bash:

```bash
colcon build --symlink-install
python3 -m pytest src/course_description/test
colcon test --event-handlers console_direct+
colcon test-result --verbose
python3 scripts/pr06_demo.py
```

Новый пакет: 14 passed. Весь workspace: 49 tests, 0 errors, 0 failures,
1 skipped — старый copyright-тест turtle_bringup. Первоначальные замечания
к отступам сценария сохранены в tests-initial.txt; конечный результат — tests.txt.
Тесты проверяют структуру дерева, ожидаемые родители и смещения сенсоров,
геометрию при другой базе/колее/радиусе, положительные инерции, check_urdf
и установленный launch из нового CLI-процесса.

Для pr06_demo.py смонтировать worktree pr06-defect в /defect:ro. Он создаёт
и останавливает собственный Xvfb, joint_states и два последовательных launch.
Оба окна RViz проверяются в контейнере на виртуальном X11-дисплее, а не через
установку ROS на macOS. Полный итог — experiment.txt; владельцы окон —
before-windows.txt и after-windows.txt. Все процессы опыта остановлены.

Источники:
https://ros.lms.ci.nsu.ru/practices/pr06 ,
https://github.com/ros/robot_state_publisher/blob/jazzy/README.md ,
https://www.ros.org/reps/rep-0103.html .
