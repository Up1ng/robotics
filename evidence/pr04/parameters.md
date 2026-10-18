# ПР04 — реальные параметры и отказ при нуле

Опыт 2026-10-18: Docker, Ubuntu 24.04.5, ROS Jazzy, Fast DDS, домен 46.
Turtlesim работал offscreen; проверены настоящий граф и команды, видимое окно
не проверялось. Точные версии и digest — `environment.txt`.

`linear_speed=0.5`, `turn_rate=0.3`, `publish_hz=10.0`.
Границы: [0, 1] м/с, [−1, 1] рад/с и [1, 30] Гц; NaN, бесконечности,
строки, bool и unset отклоняются. Допустимые целые числа приводятся к float
при заполнении Twist.

## Дефект

Отдельная ветка `pr04-defect`, коммит `f2907f4fae1061a8e4b1910fa6c011abb519ccae`:
в чистой проверке пропущена только частота. `pr04_defect.py` запускает
эту версию через PYTHONPATH=/defect/src/patrol при read-only mount worktree.
Команда `ros2 param set /patrol publish_hz 0.0` приводит к делению на ноль
в пересоздании таймера: нода завершается с кодом 1, сервис не отвечает,
CLI останавливается внешним timeout. Сырые данные — `defect.txt`,
`defect-patrol.txt`, `defect-experiment.txt`.

## Исправление

Проверка on_set не меняет состояния. Только post_set применяет уже принятые
значения; при смене частоты старый таймер отменяется и уничтожается.
SingleThreadedExecutor не выполняет callbacks двух таймеров одновременно.
Тест проверяет один оставшийся таймер. Отдельный тест добавляет следующий
валидатор с отказом: даже после успешной собственной проверки активное
состояние не меняется, если весь запрос отклонён.

Живой опыт: 40 команд при 10.000497 Гц, после обновления — 20 команд при
5.001567 Гц в четырёхсекундных окнах. Скорости стали 0.7 м/с и −0.2 рад/с.
При запросах частоты 0, −1 и NaN одновременно со скоростью 0.9 отклонён
весь пакет; get_parameters возвращает 5.0 Гц и прежние 0.7 м/с.
Измерения после отказов: 4.861620, 5.002814 и 5.000057 Гц.
Разброс отражает доставку и планирование VM, а не обещание идеального тайминга.
После возврата 10 Гц измерено 9.583468 Гц; тест допускает отклонение 0.6 Гц.

## Команды и вывод

В контейнере подключены /opt/ros/jazzy/setup.bash и install/setup.bash.
Сценарий: `python3 scripts/pr04_demo.py`; полный вывод ниже:

```text
STREAM 40 messages, Hz= 10.00049671954368
SET {'publish_hz': 5.0, 'linear_speed': 0.7, 'turn_rate': -0.2} successful= True reason= 
STREAM 20 messages, Hz= 5.001567483352138
SET {'publish_hz': 0.0, 'linear_speed': 0.9} successful= False reason= publish_hz must be finite and in [1.0, 30.0]
STREAM 19 messages, Hz= 4.8616197901548714
SET {'publish_hz': -1.0, 'linear_speed': 0.9} successful= False reason= publish_hz must be finite and in [1.0, 30.0]
STREAM 20 messages, Hz= 5.002813808929335
SET {'publish_hz': nan, 'linear_speed': 0.9} successful= False reason= publish_hz must be finite and in [1.0, 30.0]
STREAM 20 messages, Hz= 5.000056666431655
SET {'publish_hz': 10.0} successful= True reason= 
STREAM 38 messages, Hz= 9.583468189566563
$ ros2 topic type /turtle1/pose 
 turtlesim/msg/Pose
  EXIT= 0
$ ros2 param set /patrol publish_hz 5.0 
 Set parameter successful
  EXIT= 0
$ ros2 param set /patrol publish_hz 0.0 
  Setting parameter failed: publish_hz must be finite and in [1.0, 30.0]
 EXIT= 0
$ ros2 param get /patrol publish_hz 
 Double value is: 5.0
  EXIT= 0
$ ros2 service call /clear std_srvs/srv/Empty {} 
 waiting for service to become available...
requester: making request: std_srvs.srv.Empty_Request()

response:
std_srvs.srv.Empty_Response()

  EXIT= 0
$ ros2 action list -t 
 /turtle1/rotate_absolute [turtlesim/action/RotateAbsolute]
  EXIT= 0
```

В Jazzy отказ `ros2 param set` печатается в stderr, но код CLI равен 0;
поэтому сценарий проверяет также ответ parameter service, get и поток.

Сервис `/clear` выполняет один короткий запрос и возвращает ответ о завершении.
Действие `/turtle1/rotate_absolute` принимает цель поворота, допускает обратную
связь, отмену и отдельный итоговый результат длительного выполнения.

## Проверки

`tests.txt`: 29 passed. `test-result.txt`: 32 tests, 0 errors,
0 failures, 1 skipped (унаследованный copyright-тест turtle_bringup).
`tests-initial.txt` сохраняет первоначальные замечания о порядке импортов;
они исправлены до финальной проверки. ПР03 и ПР02 не переписывались.

Для повторения отказа дополнительно смонтировать worktree pr04-defect в /defect
и выполнить `python3 scripts/pr04_defect.py`; затем выполнить обычный
`python3 scripts/pr04_demo.py` без PYTHONPATH от дефектной версии.
