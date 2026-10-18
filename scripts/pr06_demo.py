"""Run real before/after tf, durability, URDF tests and RViz under Xvfb."""

import math
import os
from pathlib import Path
import re
import signal
import subprocess
import time

OUT = Path('evidence/pr06').resolve()
OUT.mkdir(parents=True, exist_ok=True)
MODEL = Path('src/course_description/urdf/vehicle.urdf.xacro').resolve()
DEFECT = Path('/defect/src/course_description/urdf/vehicle.urdf.xacro')
processes = []
handles = []


def start(name, args):
    log = (OUT / (name + '.txt')).open('w')
    handles.append(log)
    process = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT,
                               start_new_session=True)
    processes.append(process)
    return process


def stop(process):
    if process.poll() is None:
        if process.args[:2] == ['ros2', 'launch']:
            process.send_signal(signal.SIGINT)
        else:
            os.killpg(process.pid, signal.SIGINT)
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=10)


def run(log, args, expected=0, env=None, cwd=None):
    result = subprocess.run(args, capture_output=True, text=True,
                            timeout=25, env=env, cwd=cwd)
    with (OUT / log).open('a') as stream:
        stream.write('$ ' + ' '.join(map(str, args)) + '\n' + result.stdout
                     + result.stderr + '\nEXIT=' + str(result.returncode) + '\n')
    assert result.returncode == expected, (args, result.returncode, result.stderr)
    return result.stdout


def expand_and_check(label, model):
    xml = run('model-check.txt', ['xacro', str(model)])
    path = OUT / (label + '.urdf')
    path.write_text(xml)
    run('model-check.txt', ['check_urdf', str(path)])


def transform(label, expected):
    command = [
        'timeout', '6s', 'ros2', 'run', 'tf2_ros',
        'tf2_echo', 'base_link', 'lidar_link',
    ]
    text = run(label + '-tf.txt', command, expected=124)
    matches = re.findall(r'Translation: \[([^\]]+)\]', text)
    assert matches, 'No transform received'
    actual = [float(v) for v in matches[-1].split(',')]
    assert all(math.isclose(a, b, abs_tol=0.001) for a, b in zip(actual, expected))
    print(label, 'base_link -> lidar_link =', actual, flush=True)


def graph_and_screen(label):
    directory = OUT / (label + '-frames')
    directory.mkdir(exist_ok=True)
    run(label + '-frames.txt', ['ros2', 'run', 'tf2_tools', 'view_frames'], cwd=directory)
    assert list(directory.glob('*.pdf'))
    run(label + '-windows.txt', ['xwininfo', '-root', '-tree'])
    run(label + '-windows.txt', ['import', '-window', 'root', str(OUT / (label + '-rviz.png'))])


try:
    assert DEFECT.is_file(), 'Mount the committed pr06-defect source at /defect'
    for old in ['model-check.txt', 'tf-qos.txt', 'before-tf.txt', 'after-tf.txt',
                'defect-test.txt', 'fixed-test.txt', 'before-frames.txt',
                'after-frames.txt', 'before-windows.txt', 'after-windows.txt']:
        (OUT / old).unlink(missing_ok=True)
    display = os.environ.get('DISPLAY', ':99')
    start('xvfb', ['Xvfb', display, '-screen', '0', '1280x900x24', '-nolisten', 'tcp'])
    for attempt in range(30):
        if subprocess.run(['xdpyinfo'], capture_output=True).returncode == 0:
            break
        time.sleep(0.2)
    else:
        raise AssertionError('Xvfb did not become ready')
    joint_message = ('{header: auto, name: [front_left_steering_joint, '
                     'front_right_steering_joint, front_left_wheel_joint, '
                     'front_right_wheel_joint, rear_left_wheel_joint, rear_right_wheel_joint], '
                     'position: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}')
    joints = start('joint-states', ['ros2', 'topic', 'pub', '-r', '10', '/joint_states',
                                    'sensor_msgs/msg/JointState', joint_message])
    expand_and_check('before', DEFECT)
    environment = dict(os.environ, PR06_XACRO=str(DEFECT))
    test_command = [
        'python3', '-m', 'pytest', '-q',
        'src/course_description/test/test_model.py::test_lidar_parent',
    ]
    run('defect-test.txt', test_command, expected=1, env=environment)
    broken = start('before-launch', ['ros2', 'launch', 'course_description',
                                     'display.launch.py', 'model:=' + str(DEFECT)])
    time.sleep(5)
    assert broken.poll() is None
    transform('before', (0.56, 0.0, 0.76))
    graph_and_screen('before')
    stop(broken)
    time.sleep(2)
    expand_and_check('after', MODEL)
    run('fixed-test.txt', test_command)
    fixed = start('after-launch', ['ros2', 'launch', 'course_description', 'display.launch.py'])
    time.sleep(5)
    assert fixed.poll() is None
    transform('after', (0.28, 0.0, 0.38))
    graph_and_screen('after')
    # The publisher is already running and does not republish static joints periodically.
    run('tf-qos.txt', ['ros2', 'topic', 'info', '/tf_static', '--verbose',
                       '--no-daemon', '--spin-time', '3'])
    echo_command = [
        'timeout', '4s', 'ros2', 'topic', 'echo', '/tf_static', '--once',
        '--qos-reliability', 'reliable', '--qos-durability',
    ]
    latched = run('tf-qos.txt', echo_command + ['transient_local'])
    assert 'lidar_link' in latched and 'camera_link' in latched and 'imu_link' in latched
    volatile = run('tf-qos.txt', echo_command + ['volatile'], expected=124)
    assert not volatile.strip()
    run('tf-qos.txt', ['ros2', 'topic', 'info', '/tf', '--verbose',
                       '--no-daemon', '--spin-time', '3'])
    stop(fixed)
    stop(joints)
    print('PASS: check_urdf accepts both trees; semantic test fails before and passes after.',
          flush=True)
    print('PASS: late transient_local receives fixed transforms; volatile times out (124).',
          flush=True)
    print('PASS: RViz opened both models; screenshots and view_frames PDF files saved.',
          flush=True)
finally:
    for process in reversed(processes):
        stop(process)
    for handle in handles:
        handle.close()
