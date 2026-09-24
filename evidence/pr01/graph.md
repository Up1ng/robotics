# ПР01: граф `turtlesim` и разрыв домена

Дата опыта: 25.09.2026 (Asia/Novosibirsk). Среда: Docker-образ `osrf/ros:jazzy-desktop-full` (`sha256:ae7ad3ac243da1dfd8bd402a2fa08e149ffbf7a385013bd8ef798d0800accdc8`), Ubuntu 24.04.4, ROS 2 Jazzy. Все команды ниже выполнялись в одном контейнере. Симулятор A запущен с `ROS_DOMAIN_ID=16` и не перезапускался до конца опыта.

## Исправный граф

Терминал A: `ros2 run turtlesim turtlesim_node`. Терминал B: `ros2 run turtlesim turtle_teleop_key`. В B были нажаты стрелки. Терминал C использовал домен 16.

```text
$ ros2 node list --no-daemon --spin-time 2
/teleop_turtle
/turtlesim

$ ros2 topic list -t
/parameter_events [rcl_interfaces/msg/ParameterEvent]
/rosout [rcl_interfaces/msg/Log]
/turtle1/cmd_vel [geometry_msgs/msg/Twist]
/turtle1/color_sensor [turtlesim/msg/Color]
/turtle1/pose [turtlesim/msg/Pose]
```

`/teleop_turtle` публикует команды движения в `/turtle1/cmd_vel`. `/turtlesim` подписан на этот топик и публикует позу в `/turtle1/pose` и цвет под черепахой в `/turtle1/color_sensor`. `/parameter_events` и `/rosout` — стандартные топики ROS 2.

Фрагмент фактического `ros2 node info /turtlesim`:

```text
Subscribers:
  /parameter_events: rcl_interfaces/msg/ParameterEvent
  /turtle1/cmd_vel: geometry_msgs/msg/Twist
Publishers:
  /parameter_events: rcl_interfaces/msg/ParameterEvent
  /rosout: rcl_interfaces/msg/Log
  /turtle1/color_sensor: turtlesim/msg/Color
  /turtle1/pose: turtlesim/msg/Pose
```

Команда `ros2 topic type /turtle1/pose` вернула `turtlesim/msg/Pose`. Пример одного реально полученного сообщения:

```text
$ ros2 topic echo /turtle1/pose --once
x: 7.623412609100342
y: 5.608945369720459
theta: 0.03200000151991844
linear_velocity: 0.0
angular_velocity: 0.0
```

`ros2 topic hz /turtle1/pose` работала 12 секунд и была остановлена командой `timeout 12s`. Последнее окно содержало 631 сообщение; средняя частота составила **62.503 Гц** (минимальный интервал 0.015 с, максимальный 0.017 с, стандартное отклонение 0.00061 с). Код `124` здесь означает штатное завершение измерения по времени; это не результат теста разрыва связи.

## Разрыв и восстановление

В B teleop остановлен через `Ctrl+C` и повторно запущен с `ROS_DOMAIN_ID=17`. Симулятор A продолжал работать в домене 16. Стрелки в B перестали управлять черепахой. В C был установлен домен 17.

```text
$ ros2 node list --no-daemon --spin-time 2
/teleop_turtle

$ timeout 5s ros2 topic echo /turtle1/pose turtlesim/msg/Pose --once
[сообщений нет]
exit=124
```

Вывод и код возврата сохранены в `pose-broken.txt`. Тип сообщения указан явно, поскольку в чужом домене издатель позы недоступен для определения типа через ROS discovery.

После этого B снова остановлен и запущен в домене 16. В C установлен домен 16 и повторена та же проверка с тем же типом сообщения:

```text
$ ros2 node list --no-daemon --spin-time 2
/teleop_turtle
/turtlesim

$ timeout 5s ros2 topic echo /turtle1/pose turtlesim/msg/Pose --once
x: 9.670364379882812
y: 5.6744704246521
theta: 0.03200000151991844
linear_velocity: 0.0
angular_velocity: 0.0
exit=0
```

Вывод и код возврата сохранены в `pose-fixed.txt`. Координата `x` отличается от первой записи после новых нажатий стрелок в исходном домене.

| Состояние | A (симулятор) | B (teleop) | C (наблюдатель) | Видимые ноды | Поза |
| --- | ---: | ---: | ---: | --- | --- |
| До разрыва | 16 | 16 | 16 | `/teleop_turtle`, `/turtlesim` | Получена |
| Разрыв | 16 | 17 | 17 | `/teleop_turtle` | Таймаут, `exit=124` |
| После восстановления | 16 | 16 | 16 | `/teleop_turtle`, `/turtlesim` | Получена, `exit=0` |

Причина: разные значения `ROS_DOMAIN_ID` разделяют обнаружение участников DDS. Команды teleop в домене 17 не доходили до симулятора в домене 16. Переменная домена считывается при запуске процесса; для смены домена teleop пришлось перезапустить. Симулятор и установленный ROS 2 не менялись.
