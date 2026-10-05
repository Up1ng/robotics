"""Run the real PR03 graph experiment in a sourced ROS Docker shell."""

import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose

OUT = Path('evidence/pr03')
OUT.mkdir(parents=True, exist_ok=True)
processes = []
handles = []


def start(label, args):
    log = (OUT / (label + '.txt')).open('w')
    handles.append(log)
    process = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT,
                               start_new_session=True)
    processes.append(process)
    return process


def stop(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGINT)
        process.wait(timeout=10)


def cli(label, args, timeout=15):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    (OUT / (label + '.txt')).write_text(
        '$ ' + ' '.join(args) + '\n' + result.stdout + result.stderr
        + '\nEXIT=' + str(result.returncode) + '\n')
    assert result.returncode == 0, (label, result.stderr)
    return result.stdout


rclpy.init()
probe = Node('pr03_probe')
poses = []
wrong = []
correct = []


def pose_received(msg):
    poses.append({'time': time.monotonic(), 'x': msg.x, 'y': msg.y,
                  'theta': msg.theta, 'linear_velocity': msg.linear_velocity,
                  'angular_velocity': msg.angular_velocity})


def twist_received(target, msg):
    target.append({'time': time.monotonic(), 'linear_x': msg.linear.x,
                   'angular_z': msg.angular.z})


subscriptions = [
    probe.create_subscription(Pose, '/turtle1/pose', pose_received, 10),
    probe.create_subscription(Twist, '/cmd_vel', lambda m: twist_received(wrong, m), 10),
    probe.create_subscription(Twist, '/turtle1/cmd_vel',
                              lambda m: twist_received(correct, m), 10),
]


def observe(duration):
    end = time.monotonic() + duration
    while time.monotonic() < end:
        rclpy.spin_once(probe, timeout_sec=max(0, min(0.05, end - time.monotonic())))


def pose_delta(samples):
    return math.hypot(samples[-1]['x'] - samples[0]['x'],
                      samples[-1]['y'] - samples[0]['y'])


try:
    patrol = start('patrol-broken', ['ros2', 'run', 'patrol', 'patrol'])
    observe(3)
    no_pose = wrong.copy()
    assert len(no_pose) >= 5
    assert all(m['linear_x'] == 0 and m['angular_z'] == 0 for m in no_pose)
    simulator = start('turtlesim', ['ros2', 'launch', 'turtle_bringup', 'sim.launch.py'])
    observe(3)
    assert poses, 'No turtlesim pose; inspect turtlesim.txt'
    cli('pose-type', ['ros2', 'topic', 'type', '/turtle1/pose'])
    cli('nodes-broken', ['ros2', 'node', 'list'])
    cli('patrol-info-broken', ['ros2', 'node', 'info', '/patrol'])
    cli('topic-info-broken', ['ros2', 'topic', 'info', '/cmd_vel', '--verbose'])
    cli('turtle-topic-broken', ['ros2', 'topic', 'info', '/turtle1/cmd_vel', '--verbose'])
    poses.clear()
    wrong.clear()
    correct.clear()
    observe(10)
    broken = {'duration_s': 10, 'poses': poses.copy(), 'commands': wrong.copy(),
              'turtle_commands': correct.copy(), 'displacement': pose_delta(poses)}
    assert len(wrong) >= 90
    assert not correct
    assert broken['displacement'] < 1e-5
    assert all(m['linear_x'] == 0.5 and m['angular_z'] == 0.3 for m in wrong)
    stop(patrol)
    fixed = start('patrol-fixed', ['ros2', 'run', 'patrol', 'patrol', '--ros-args',
                                   '-r', 'cmd_vel:=/turtle1/cmd_vel'])
    observe(3)
    cli('patrol-info-fixed', ['ros2', 'node', 'info', '/patrol'])
    cli('topic-info-fixed', ['ros2', 'topic', 'info', '/turtle1/cmd_vel', '--verbose'])
    hz = start('topic-hz', ['ros2', 'topic', 'hz', '/turtle1/cmd_vel', '--window', '100'])
    observe(1)  # Drain callbacks queued during the blocking CLI inspection.
    poses.clear()
    correct.clear()
    before = time.monotonic()
    observe(10)
    elapsed = time.monotonic() - before
    samples = correct.copy()
    stop(hz)
    rate = (len(samples) - 1) / (samples[-1]['time'] - samples[0]['time'])
    repaired = {'duration_s': elapsed, 'poses': poses.copy(), 'commands': samples,
                'displacement': pose_delta(poses), 'rate_hz': rate}
    assert len(samples) >= 90
    assert 9.5 <= rate <= 10.5
    assert repaired['displacement'] > 0.5
    assert all(m['linear_x'] == 0.5 and m['angular_z'] == 0.3 for m in samples)
    poses.clear()
    correct.clear()
    stopped_at = time.monotonic()
    stop(fixed)
    observe(3)
    shutdown = {'signal_time': stopped_at, 'process_returncode': fixed.returncode,
                'poses': poses.copy(), 'commands': correct.copy()}
    assert poses[-1]['linear_velocity'] == 0
    assert poses[-1]['angular_velocity'] == 0
    assert pose_delta(poses[-30:]) < 1e-5
    stopped_pose = next(p for p in poses if p['linear_velocity'] == 0
                        and p['angular_velocity'] == 0)
    shutdown['stop_delay_s'] = stopped_pose['time'] - stopped_at
    cli('nodes-after-patrol-stop', ['ros2', 'node', 'list'])
    stop(simulator)
    result = {'no_pose_commands': no_pose, 'broken': broken,
              'fixed': repaired, 'shutdown': shutdown}
    (OUT / 'measurements.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'no_pose_zero_count': len(no_pose),
                      'broken_displacement': broken['displacement'],
                      'fixed_displacement': repaired['displacement'],
                      'fixed_command_count': len(samples), 'rate_hz': rate,
                      'stop_delay_s': shutdown['stop_delay_s']}, indent=2))
finally:
    for process in reversed(processes):
        stop(process)
    for handle in handles:
        handle.close()
    probe.destroy_node()
    rclpy.shutdown()
