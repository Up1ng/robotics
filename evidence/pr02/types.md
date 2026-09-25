# ПР02 — типы сообщений

Фактические типы получены командами `ros2 topic type /turtle1/pose`, `ros2 topic type /turtle1/cmd_vel` и `ros2 interface show geometry_msgs/msg/Twist` ([сырой вывод](interface.txt)).

| Топик | Тип | Назначение |
| --- | --- | --- |
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | Команда движения, которую читает `/turtlesim`. |
| `/turtle1/pose` | `turtlesim/msg/Pose` | Текущее положение, ориентация и скорости черепахи. |

`Twist.linear` и `Twist.angular` — трёхмерные векторы с полями `x`, `y`, `z` типа `float64`. В опыте `linear.x=1.0` задаёт движение вперёд, `angular.z=0.5` — поворот; остальные компоненты равны нулю. В `Pose` поля `x` и `y` задают координаты, `theta` — ориентацию, `linear_velocity` и `angular_velocity` — текущие скорости. После единичной команды скорости вновь стали нулевыми, но координаты и угол остались изменёнными.

Ошибочный топик `/cmd_vel` имел тот же тип `Twist`, однако не имел подписчика; его сообщение не попало в `/turtlesim`.
