# ПР01 — окружение и граф ROS 2

Цель работы: запустить готовый `turtlesim`, описать узлы и топики, измерить частоту `/turtle1/pose`, затем воспроизвести разрыв связи из-за разных `ROS_DOMAIN_ID` и восстановить связь.

## Среда

Используйте одну из поддерживаемых связок: Ubuntu 24.04 + ROS 2 Jazzy или Ubuntu 26.04 + ROS 2 Lyrical. Для опыта нужны `turtlesim`, три терминала в одной среде и курс-комплект `v1` с шаблоном отчёта и checker. Этот опыт выполнен в официальном Docker-образе `osrf/ros:jazzy-desktop-full` с зафиксированным digest `sha256:ae7ad3ac243da1dfd8bd402a2fa08e149ffbf7a385013bd8ef798d0800accdc8`. Для аудитории замените домены 16 и 17 на выделенную пару.

Скриншоты задания лежат в `скрины_сайта_курса/`. Они не являются результатами опыта.

## 1. Подготовка

На хосте из корня репозитория запустите контейнер. Доступ к X-серверу нужен окну `turtlesim`:

```bash
xhost +si:localuser:root
sudo docker run -d --rm --name nsu-pr01 --network host --ipc host \
  -e DISPLAY="$DISPLAY" -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$PWD":/workspace -w /workspace \
  osrf/ros:jazzy-desktop-full@sha256:ae7ad3ac243da1dfd8bd402a2fa08e149ffbf7a385013bd8ef798d0800accdc8 \
  sleep infinity
```

Откройте три терминала на хосте и в каждом войдите в **этот же** контейнер через `sudo docker exec -it nsu-pr01 bash`. В каждом терминале контейнера выполните:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=16
```

В терминале C, из корня репозитория:

```bash
mkdir -p evidence/pr01
ros2 doctor --report > evidence/pr01/doctor.txt 2>&1
```

## 2. Исправный граф

В терминале A запустите `ros2 run turtlesim turtlesim_node`. В терминале B запустите `ros2 run turtlesim turtle_teleop_key` и нажмите стрелки в этом терминале. В терминале C последовательно выполните:

```bash
ros2 node list --no-daemon --spin-time 2
ros2 topic list -t
ros2 node info /turtlesim
ros2 topic type /turtle1/pose
ros2 topic echo /turtle1/pose --once
ros2 topic hz /turtle1/pose
```

Последнюю команду оставьте работать не менее 10 секунд и завершите `Ctrl+C`. Сохраните реальные выводы и составьте `evidence/pr01/graph.md`: команды и их вывод, роли узлов, полные имена и типы топиков, фактическую частоту и длительность измерения. На Jazzy тип позы обычно `turtlesim/msg/Pose`, на Lyrical — `turtlesim_msgs/msg/Pose`; запишите фактический результат команды. Команда движения публикуется в `/turtle1/cmd_vel`.

## 3. Разрыв и восстановление связи

Терминал A оставьте работающим в домене 16. В B остановите teleop через `Ctrl+C`, затем запустите его снова в другом домене:

```bash
export ROS_DOMAIN_ID=17
ros2 run turtlesim turtle_teleop_key
```

Стрелки больше не должны двигать черепаху. В C переключитесь в домен 17 и сохраните наблюдение:

```bash
POSE_TYPE=$(ROS_DOMAIN_ID=16 ros2 topic type /turtle1/pose)
export ROS_DOMAIN_ID=17
ros2 node list --no-daemon --spin-time 2
timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once > evidence/pr01/pose-broken.txt 2>&1
printf 'exit=%s\n' "$?" >> evidence/pr01/pose-broken.txt
```

Для истечения времени ожидается `exit=124`. Верните B в домен 16: остановите teleop, выполните `export ROS_DOMAIN_ID=16` и запустите `ros2 run turtlesim turtle_teleop_key` снова. В C повторите тот же тест:

```bash
export ROS_DOMAIN_ID=16
ros2 node list --no-daemon --spin-time 2
timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once > evidence/pr01/pose-fixed.txt 2>&1
printf 'exit=%s\n' "$?" >> evidence/pr01/pose-fixed.txt
```

Ожидается фактическое сообщение позы и `exit=0`. Если обнаружение узлов ещё идёт, повторите проверку. Не заменяйте ошибку импорта или иной код возврата на `124`.

В `graph.md` сравните состояния «до / разрыв / после», домены участников, коды возврата и причину: `ROS_DOMAIN_ID` устанавливается при запуске процесса, поэтому смена переменной в терминале не меняет уже работающий teleop. Симулятор и установленный ROS перезапускать не требуется.

## 4. Отчёт и проверка

В `evidence/pr01/environment.json` вручную запишите фактические способ запуска (`native`, `wsl2` или `docker`), версию ОС **в контейнере**, дистрибутив ROS, версию Gazebo, RMW и домены опыта. Для Docker добавьте digest образа. Используйте `/etc/os-release`, `ros2 doctor --report`, `gz sim --versions` и вывод своих команд. Не сохраняйте секреты и полный дамп переменных среды.

Архив course-kit `v1-w02` закреплён в `.github/ci/course-kit-v1-w02.tar.gz` (SHA-256 `5d210c431e32418f45e2cffa9dd2028116c7a9520a36f3c7079c778cd73437a8`). Распакуйте его в `.course-kit/v1/`. Скопируйте `.course-kit/v1/practices/templates/report.json` в `evidence/pr01/report.json`, замените все `replace-with-*`, укажите полный SHA коммита реализации, реальные команды и проверки, а также claims из манифеста ПР01. Если использовался ИИ, заполните `AI_USAGE.md` по шаблону комплекта. CI проверяет хэш архива и запускает checker из него.

Комплект предоставлен курсом «Робототехника» НГУ; источник — `https://ros.lms.ci.nsu.ru/`. Архив включён без изменений для воспроизводимой проверки. Условия повторного использования указаны в `v1/LICENSE.md` внутри архива: код — Apache License 2.0, тексты — Creative Commons Attribution 4.0 International.

Проверьте файлы:

```bash
python3 -m json.tool evidence/pr01/environment.json > /dev/null
python3 .course-kit/v1/tools/check_practice.py PR01 --submission .
```

По порядку сдачи сначала фиксируется коммит README и CI workflow, затем отдельным коммитом добавляется `evidence/pr01/`. Для сдачи нужны ссылка на личный GitHub/GitVerse репозиторий, полный SHA коммита с evidence и ссылка на успешный run встроенного CI с доступным логом. Проверка файлов не заменяет повторение живого опыта на защите.

После опыта закройте интерактивные процессы и остановите контейнер на хосте: `sudo docker stop nsu-pr01`. Если больше не нужен доступ root к X-серверу, выполните `xhost -si:localuser:root`.
