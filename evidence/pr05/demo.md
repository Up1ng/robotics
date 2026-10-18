# ПР05 — реальный launch, несовместимый QoS и один MCAP

Опыт 2026-10-18: Docker ROS 2 Jazzy, Fast DDS, домен 56, Linux arm64.
Точные версии и digest — environment.txt. Turtlesim работал offscreen;
проверены граф, сообщения и команды, видимое окно на экране не проверялось.

## Запуск и имена

`python3 scripts/pr05_demo.py` запускает course_bringup/patrol.launch.py.
Аргументы namespace, record, bag_dir и subscriber_reliability разрешаются
при запуске. Recorder ограждён IfCondition; в первой фазе record=false
и отсутствие rosbag2_recorder проверено через список узлов.

Один глобальный /turtlesim, контроллер /robot_a/patrol, relay
/robot_a/pose_relay и наблюдатель /robot_a/pose_subscriber.
Топики внутри нод относительные; launch remap связывает pose с /turtle1/pose,
а cmd_vel с /turtle1/cmd_vel. Relay предлагает best_effort, volatile,
keep_last depth=10 и automatic liveliness.

## Дефект и исправление на живом потоке

Первая команда:

```bash
ros2 launch course_bringup patrol.launch.py namespace:=robot_a \
  subscriber_reliability:=reliable record:=false bag_dir:=evidence/pr05/bag
timeout 5s ros2 topic echo /robot_a/sensor_pose --qos-reliability reliable --once
```

Топик присутствует, но reliability запрошена выше предложенной.
Наблюдатель получает 0 сообщений, echo завершается по timeout (124).
Логи предупреждают о несовместимой политике RELIABILITY.
Сырые endpoints, команды и коды завершения — qos-before.txt, launch-before.txt.

После остановки первой системы запущена та же конфигурация с
subscriber_reliability:=best_effort и record:=true. Наблюдатель и echo
получают позы, echo возвращает 0; логи — launch-after.txt и qos-after.txt.
Регистрируется только /robot_a/sensor_pose, без дополнительных топиков.
SIGINT отправляется самому launch, который один раз завершает дочерние
процессы и recorder. Финальный launch-after.txt подтверждает чистое завершение.

## Запись и повтор

Один bag: 990 сообщений turtlesim/msg/Pose за 15.919945555 с, storage mcap,
ровно один топик /robot_a/sensor_pose. `bag-metadata.yaml` — точная копия
`bag/metadata.yaml`; `ros2 bag info` включён в qos-after.txt.
Сам MCAP сохранён в bag/bag_0.mcap, SHA-256 — bag-sha256.txt.

Живой launch остановлен; проверено отсутствие /turtlesim и pose_relay.
Для обоих сравнений проигрывается этот же bag с одним и тем же override:

```bash
ros2 bag play evidence/pr05/bag --loop \
  --qos-profile-overrides-path config/qos-overrides.yaml
```

Player предлагает best_effort. Reliable-подписчик снова получает 0 сообщений,
echo завершается с 124. Затем тот же файл повторно проигран с тем же override:
best_effort-подписчик и echo получают сообщения (echo: 0).
Наборы входных данных для сравнения не менялись; второй bag не создавался.
Флаги --no-daemon --spin-time 3 в диагностике дают discovery завершиться,
не используя старое состояние CLI daemon.

Максимальные реальные счётчики наблюдателя:

```json
{
  "launch-before": 0,
  "launch-after": 968,
  "replay-subscriber-reliable": 0,
  "replay-subscriber-best_effort": 431
}
```

## Проверки

`tests.txt`: 32 passed, включая smoke-тест установленного launch из нового
процесса CLI. `test-result.txt`: 35 tests, 0 errors, 0 failures, 1 skipped
(унаследованный copyright-тест turtle_bringup).
`experiment.txt` подтверждает все assertions живого опыта и replay.
`tests-initial.txt` сохраняет первоначальные замечания тестов;
`experiment-initial.txt` и `launch-initial.txt` — прежний слишком ранний
запрос discovery и повторный SIGINT при завершении всей группы.
В финальном сценарии discovery явное, а launch получает один сигнал.
Это ошибки первоначального сценария, а требуемый дефект — несовместимый QoS.

ПР04 сохранена как предок этой ветки; её исходные evidence не переписывались.
Для нового опыта сначала перенести существующий каталог bag: сценарий
отказывается перезаписывать запись. Для просмотра уже готового результата
достаточно ros2 bag info и bag play с указанным override.
