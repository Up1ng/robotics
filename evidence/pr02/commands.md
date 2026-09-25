# ПР02 — команды и наблюдения

Опыт выполнен в одном контейнере `osrf/ros:jazzy-desktop-full` с `ROS_DOMAIN_ID=26`. Рабочий каталог контейнера — `/workspace`, смонтированный корень репозитория. До запуска launch прежние экземпляры turtlesim не работали.

## Навигация и сборка

Три использованные команды Linux:

| Команда | Назначение | Фактический результат |
| --- | --- | --- |
| `pwd` | Показать текущий каталог | `/workspace` — корень смонтированного репозитория. |
| `mkdir -p src evidence/pr02` | Создать каталоги исходников и evidence | Каталоги созданы; команда ничего не вывела. |
| `cat src/turtle_bringup/package.xml` | Прочитать метаданные пакета | Показаны имя `turtle_bringup`, лицензия `Apache-2.0` и зависимости `launch`, `launch_ros`, `turtlesim`. |

`>` заменяет содержимое файла выводом одной команды; `|` передаёт stdout следующей программе, поэтому `2>&1 | tee evidence/pr02/build.txt` одновременно показало сборку и записало stdout/stderr в файл. `source /opt/ros/jazzy/setup.bash` меняет окружение текущего Bash, а запуск нового процесса не может изменить окружение родительского терминала.

Пакет создан через `ros2 pkg create --build-type ament_python --license Apache-2.0 turtle_bringup --dependencies launch launch_ros turtlesim`. До добавления launch выполнено `colcon build --symlink-install --packages-select turtle_bringup`: результат `1 package finished`, [полный лог](build-empty.txt). Пустой пакет находился в `/workspace/install/turtle_bringup`, но не содержал launch-файла и собственной ноды.

После добавления `launch/sim.launch.py` и записи его в `setup.py` та же сборка завершилась `1 package finished`, [итоговый лог](build.txt). После `source install/setup.bash` команда `ros2 pkg prefix turtle_bringup` вернула `/workspace/install/turtle_bringup`; файл `share/turtle_bringup/launch/sim.launch.py` там найден. Таким образом, launch установлен как ресурс пакета, а не только лежит в `src/`.

## Запуск и остановка

В терминале A выполнено `ros2 launch turtle_bringup sim.launch.py`: [лог](launch.txt) показывает запуск `turtlesim_node`, а `ros2 node list --no-daemon --spin-time 2` в терминале C показал `/turtlesim`. Команда `ros2 topic type /turtle1/pose` вернула `turtlesim/msg/Pose`.

После опыта launch остановлен сигналом `SIGINT` (эквивалент `Ctrl+C`). Лог показывает чистое завершение `turtlesim_node`; повторный `ros2 node list --no-daemon --spin-time 2` не вывел нод.

## Неверное имя топика и исправление

Исходная поза по `ros2 topic echo /turtle1/pose --once`: `x=5.544444561004639`, `y=5.544444561004639`, `theta=0.0` ([вывод](pose-before.txt)).

В терминале B запущено:

```bash
timeout 12s ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

[Вывод издателя](wrong-pub.txt) содержит 11 публикаций и `exit=124` от `timeout`. Пока он работал, `ros2 topic info /cmd_vel --verbose` показал **1 издателя и 0 подписчиков**, а `ros2 topic info /turtle1/cmd_vel --verbose` — **0 издателей и 1 подписчика `/turtlesim`** ([оба вывода](topic-info-broken.txt)). Поза осталась `x=5.544444561004639`, `y=5.544444561004639`, `theta=0.0` ([вывод](pose-broken.txt)).

После остановки ошибочного издателя изменено только имя топика:

```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

Команда опубликовала один `Twist` ([вывод](correct-pub.txt)). Повторная проверка позы дала `x=6.523256778717041`, `y=5.8048295974731445`, `theta=0.5120000243186951` ([вывод](pose-fixed.txt)): черепаха сместилась и повернулась в ожидаемую сторону. Одной публикации хватило для ограниченного движения; без новых команд черепаха остановилась.

Причина сбоя — различие **полных имён** `/cmd_vel` и `/turtle1/cmd_vel`. Совпадающий тип `geometry_msgs/msg/Twist` сам по себе не соединяет издателя с подписчиком; DDS связывает конечные точки одного имени и совместимого типа. ROS и симулятор менять не требовалось.
