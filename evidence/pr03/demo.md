# ПР03: демонстрация ноды и разрыва имени топика

## Среда и запуск

Опыт выполнен 2026-10-05 в Docker, ROS 2 Jazzy, домен 36.
Фактические версии: `environment.txt`; digest образа: `docker-image.txt`.
Course-kit `v1-w05`, SHA-256
`bca214e3de6f90f9513049dfa0f36fee65ad834da502dc3f3f8fb443517b5197`.
Workspace продолжает ПР02, пакет `turtle_bringup` сохранён.

В контейнере из корня рабочего дерева:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
python3 -m pytest src/patrol/test
colcon test --event-handlers console_direct+
colcon test-result --verbose
python3 scripts/pr03_demo.py
```

Сценарий запускает настоящие `ros2 run patrol patrol` и
`ros2 launch turtle_bringup sim.launch.py`. GUI turtlesim работал через X11
(`DISPLAY=:1`); окно TurtleSim наблюдалось через `xwininfo`.
В логе присутствуют предупреждения Mesa об аппаратном драйвере; получение
позы и движение при этом подтверждены измерениями.

## Собрать

`ros2 pkg create --build-type ament_python --node-name patrol patrol
--dependencies rclpy geometry_msgs turtlesim` выполнена в Docker.
Тип `/turtle1/pose` проверен CLI: `turtlesim/msg/Pose` (`pose-type.txt`).
`rclpy.init` создаёт ROS-контекст. Объект `Patrol` создаёт издателя, подписку
и таймер. Подписка сохранена в `self.subscription`; её callback только
присваивает `self.last_pose`. Таймер каждые 0,1 с вызывает чистую функцию
`command_for_pose` и публикует её результат. До первой позы все поля нулевые;
после позы только `linear.x=0.5` и `angular.z=0.3` ненулевые.
`rclpy.spin` обслуживает события, вызывая callbacks при сообщениях и таймере.
Callback не работает отдельным бесконечным циклом и не блокирует executor.

До запуска симулятора получено 20 нулевых команд.
Тесты проверяют отсутствие позы, обычную позу, остальные нулевые поля,
отсутствие изменения входа и независимость возвращённых сообщений.
Функциональные тесты не требуют `init` или `spin`.

## Сломать

```bash
ros2 run patrol patrol
ros2 node info /patrol
ros2 topic info /cmd_vel --verbose
ros2 topic info /turtle1/cmd_vel --verbose
```

Относительный `cmd_vel` у узла в корневом namespace разрешается в `/cmd_vel`.
У turtlesim другое имя: `/turtle1/cmd_vel`. В `topic-info-broken.txt` единственный
подписчик `/cmd_vel` — измерительный `/pr03_probe`, а не turtlesim.
В `turtle-topic-broken.txt` у `/turtle1/cmd_vel` нет издателя.
Тип и QoS совпадают; причина разрыва — имя, не QoS и не ROS_DOMAIN_ID.

За 10 секунд получено 110 команд в `/cmd_vel`, но 0 команд
в `/turtle1/cmd_vel`. Поза поступает (635 сообщений), смещение
черепахи равно 0.000000. Обычные команды ненулевые — значит
нулевое движение объясняется разрывом связи, а не отсутствием позы.

## Доказать

После Ctrl+C у ошибочного patrol тот же исполняемый файл запущен с remap:

```bash
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
ros2 node info /patrol
ros2 topic info /turtle1/cmd_vel --verbose
ros2 topic hz /turtle1/cmd_vel --window 100
```

`topic-info-fixed.txt` показывает издателя patrol и подписчиков turtlesim и
probe. Исходник не менялся между фазами, изменилось только соответствие имени.
За 10.000417 с получено 100 команд, измеренная
частота по монотонным отметкам приёма — 9.999796 Гц.
Формула: `(N-1)/(t_last-t_first)`. Отдельный CLI `ros2 topic hz` работал
в том же десятисекундном окне; его сырые измерения — `topic-hz.txt`.
Очередь probe после блокирующих CLI-команд обработана до начала окна.
Смещение за окно — 3.324411, поза получена 625 раз.

## Ctrl+C и остановка

Ctrl+C посылает SIGINT. `spin` заканчивается через исключение;
`finally` уничтожает ноду и закрывает ROS-контекст, если он ещё работает.
В сценарии SIGINT отправлен группе собственных процессов, как при Ctrl+C
в терминале. Он не является нулевым Twist: нода не публикует тормозную команду
при завершении. Turtlesim сам обнуляет скорость после таймаута отсутствия команд.

После сигнала нода завершилась с кодом 0; первая поза
с обеими нулевыми скоростями получена через 0.937599 с.
Затем проверено, что последние 30 поз не меняются. После остановки patrol
в графе остались turtlesim и probe (`nodes-after-patrol-stop.txt`),
после измерения остановлен и launch. Все процессы сценария очищаются в finally.
Временный доступ X11 отзывается по окончании работы.

## Проверки и логи

`measurements.json` содержит реальные сообщения и монотонные времена всех фаз;
`experiment.txt` — краткий результат успешного сценария. `build.txt`,
`tests.txt`, `colcon-test.txt`, `test-result.txt` подтверждают сборку и тесты.
В patrol тест copyright включён. В сохранённом пакете ПР02 его шаблонный
copyright-тест по-прежнему skipped; функциональные тесты patrol не пропущены.

`tests-initial.txt` сохраняет первоначальный отказ линтера: порядок импортов
и отступ сценария. Это исправлено до сдачи. `experiment-initial.txt` сохраняет
первое измерение с очередью сообщений на границе окна; оно не используется
для итоговой частоты. Повтор после исправления границы содержит 100 команд.

Обязательная часть выполнена; необязательный маршрут мышью не реализован.
