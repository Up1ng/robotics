"""Measure a real parameter service and command stream; run inside ROS Docker."""

import json
import os
from pathlib import Path
import signal
import subprocess
import time

from geometry_msgs.msg import Twist
from rcl_interfaces.srv import GetParameters, SetParametersAtomically
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter

OUT = Path('evidence/pr04')
OUT.mkdir(parents=True, exist_ok=True)
rclpy.init()
probe = Node('pr04_probe')
samples = []
sub = probe.create_subscription(Twist, '/turtle1/cmd_vel',
                                lambda msg: samples.append((time.monotonic(), msg)), 10)
handles = []
processes = []


def start(name, args):
    log = (OUT / (name + '.txt')).open('w')
    handles.append(log)
    p = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    processes.append(p)
    return p


def observe(seconds):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        rclpy.spin_once(probe, timeout_sec=0.02)


def call(client, request):
    assert client.wait_for_service(timeout_sec=15)
    future = client.call_async(request)
    rclpy.spin_until_future_complete(probe, future, timeout_sec=10)
    assert future.done(), 'Parameter service timeout'
    return future.result()


def update(**values):
    request = SetParametersAtomically.Request()
    request.parameters = [Parameter(k, value=v).to_parameter_msg() for k, v in values.items()]
    result = call(setter, request).result
    print('SET', values, 'successful=', result.successful, 'reason=', result.reason, flush=True)
    return result.successful


def measure(expected):
    observe(0.5)
    samples.clear()
    observe(4)
    rate = (len(samples) - 1) / (samples[-1][0] - samples[0][0])
    assert abs(rate - expected) < 0.6, (rate, expected)
    print('STREAM', len(samples), 'messages, Hz=', rate, flush=True)
    return {'count': len(samples), 'hz': rate}


try:
    start('turtlesim', ['ros2', 'run', 'turtlesim', 'turtlesim_node'])
    start('patrol', ['ros2', 'run', 'patrol', 'patrol', '--ros-args',
                     '-r', 'pose:=/turtle1/pose', '-r', 'cmd_vel:=/turtle1/cmd_vel'])
    setter = probe.create_client(SetParametersAtomically, '/patrol/set_parameters_atomically')
    getter = probe.create_client(GetParameters, '/patrol/get_parameters')
    assert setter.wait_for_service(timeout_sec=20)
    results = {'initial': measure(10)}
    assert update(publish_hz=5.0, linear_speed=0.7, turn_rate=-0.2)
    results['updated'] = measure(5)
    assert all(m.linear.x == 0.7 and m.angular.z == -0.2 for _, m in samples)
    for value in (0.0, -1.0, float('nan')):
        assert not update(publish_hz=value, linear_speed=0.9)
        response = call(getter, GetParameters.Request(names=['publish_hz', 'linear_speed']))
        assert [p.double_value for p in response.values] == [5.0, 0.7]
        measure(5)
        assert all(m.linear.x == 0.7 for _, m in samples)
    assert update(publish_hz=10.0)
    results['restored'] = measure(10)
    for args in (['ros2', 'topic', 'type', '/turtle1/pose'],
                 ['ros2', 'param', 'set', '/patrol', 'publish_hz', '5.0'],
                 ['ros2', 'param', 'set', '/patrol', 'publish_hz', '0.0'],
                 ['ros2', 'param', 'get', '/patrol', 'publish_hz'],
                 ['ros2', 'service', 'call', '/clear', 'std_srvs/srv/Empty', '{}'],
                 ['ros2', 'action', 'list', '-t']):
        r = subprocess.run(args, capture_output=True, text=True, timeout=20)
        print('$', ' '.join(args), '\n', r.stdout, r.stderr, 'EXIT=', r.returncode, flush=True)
        assert r.returncode == 0
    (OUT / 'measurements.json').write_text(json.dumps(results, indent=2) + '\n')
finally:
    for p in reversed(processes):
        if p.poll() is None:
            os.killpg(p.pid, signal.SIGINT)
            p.wait(timeout=15)
    for h in handles:
        h.close()
    probe.destroy_node()
    rclpy.shutdown()
