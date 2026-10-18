"""Exercise launch, live QoS, MCAP and both QoS requests on the same replay."""

import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

import yaml

OUT = Path('evidence/pr05')
OUT.mkdir(parents=True, exist_ok=True)
BAG = OUT / 'bag'
if BAG.exists():
    raise SystemExit('Bag already exists; move it aside before generating a new experiment.')
processes = []
handles = []
before = (OUT / 'qos-before.txt').open('w')
after = (OUT / 'qos-after.txt').open('w')


def start(label, args):
    log = (OUT / (label + '.txt')).open('w')
    handles.append(log)
    p = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    processes.append(p)
    return p


def stop(p):
    if p.poll() is None:
        if p.args[:2] == ['ros2', 'launch']:
            p.send_signal(signal.SIGINT)  # launch forwards the signal to its children.
        else:
            os.killpg(p.pid, signal.SIGINT)
        try:
            p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGTERM)
            p.wait(timeout=10)


def cli(log, args, expected=0):
    if args[:3] in (['ros2', 'node', 'list'], ['ros2', 'topic', 'list'],
                    ['ros2', 'topic', 'info']):
        args = args + ['--no-daemon', '--spin-time', '3']
    r = subprocess.run(args, capture_output=True, text=True, timeout=30)
    log.write('$ ' + ' '.join(args) + '\n' + r.stdout + r.stderr
              + '\nEXIT=' + str(r.returncode) + '\n')
    log.flush()
    assert r.returncode == expected, (args, r.returncode, r.stderr)
    return r.stdout


def echo(log, policy, expected):
    return cli(log, ['timeout', '5s', 'ros2', 'topic', 'echo', '/robot_a/sensor_pose',
                     '--qos-reliability', policy, '--once'], expected)


def launch(policy, record):
    return ['ros2', 'launch', 'course_bringup', 'patrol.launch.py',
            'namespace:=robot_a', 'subscriber_reliability:=' + policy,
            'record:=' + record, 'bag_dir:=' + str(BAG)]


try:
    broken = start('launch-before', launch('reliable', 'false'))
    time.sleep(5)
    assert broken.poll() is None
    nodes = cli(before, ['ros2', 'node', 'list'])
    assert '/robot_a/pose_relay' in nodes and '/robot_a/patrol' in nodes
    assert '/robot_a/pose_subscriber' in nodes
    assert 'rosbag2_recorder' not in nodes
    cli(before, ['ros2', 'topic', 'list', '-t'])
    cli(before, ['ros2', 'topic', 'info', '/robot_a/sensor_pose', '--verbose'])
    assert echo(before, 'reliable', 124) == ''
    stop(broken)
    assert 'received=0' in (OUT / 'launch-before.txt').read_text()
    time.sleep(2)
    fixed = start('launch-after', launch('best_effort', 'true'))
    time.sleep(5)
    assert fixed.poll() is None
    cli(after, ['ros2', 'node', 'list'])
    cli(after, ['ros2', 'topic', 'info', '/robot_a/sensor_pose', '--verbose'])
    assert 'x:' in echo(after, 'best_effort', 0)
    time.sleep(3)
    stop(fixed)
    import re
    assert any(int(n) > 0 for n in re.findall(
        r'received=(\d+)', (OUT / 'launch-after.txt').read_text()))
    time.sleep(2)
    assert (BAG / 'metadata.yaml').is_file()
    metadata = yaml.safe_load((BAG / 'metadata.yaml').read_text())['rosbag2_bagfile_information']
    topics = metadata['topics_with_message_count']
    assert len(topics) == 1
    assert topics[0]['topic_metadata']['name'] == '/robot_a/sensor_pose'
    assert topics[0]['message_count'] > 50
    assert metadata['storage_identifier'] == 'mcap'
    shutil.copyfile(BAG / 'metadata.yaml', OUT / 'bag-metadata.yaml')
    cli(after, ['ros2', 'bag', 'info', str(BAG)])
    # No live source remains; only the player publishes during the following checks.
    nodes = cli(after, ['ros2', 'node', 'list'])
    assert '/robot_a/pose_relay' not in nodes
    assert '/turtlesim' not in nodes
    for policy, log, expected in [('reliable', before, 124), ('best_effort', after, 0)]:
        log.write('\nREPLAY: same bag and same best_effort publisher override\n')
        subscriber = start('replay-subscriber-' + policy,
                           ['ros2', 'run', 'patrol', 'pose_subscriber', '--ros-args',
                            '-r', '__ns:=/robot_a', '-p', 'reliability:=' + policy])
        player = start('replay-' + policy,
                       ['ros2', 'bag', 'play', str(BAG), '--loop',
                        '--qos-profile-overrides-path', 'config/qos-overrides.yaml'])
        time.sleep(3)
        assert player.poll() is None
        cli(log, ['ros2', 'topic', 'info', '/robot_a/sensor_pose', '--verbose'])
        output = echo(log, policy, expected)
        assert ('x:' in output) if expected == 0 else output == ''
        stop(player)
        stop(subscriber)
        counts = [int(n) for n in re.findall(
            r'received=(\d+)', (OUT / ('replay-subscriber-' + policy + '.txt')).read_text())]
        assert counts
        assert max(counts) > 0 if expected == 0 else max(counts) == 0
        time.sleep(2)
    print('PASS: record=false, namespace, incompatible live QoS, fixed live delivery,')
    print('one MCAP stream; reliable timeout and best_effort delivery on the same bag.')
finally:
    for p in reversed(processes):
        stop(p)
    for handle in handles + [before, after]:
        handle.close()
