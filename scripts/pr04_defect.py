"""Run only against the intentional pr04-defect source mounted at /defect."""

import os
from pathlib import Path
import signal
import subprocess
import time

from rcl_interfaces.srv import GetParameters
import rclpy
from rclpy.node import Node

out = Path('evidence/pr04')
out.mkdir(parents=True, exist_ok=True)
log = (out / 'defect-patrol.txt').open('w')
environment = dict(os.environ)
environment['PYTHONPATH'] = '/defect/src/patrol:' + environment.get('PYTHONPATH', '')
process = subprocess.Popen(['ros2', 'run', 'patrol', 'patrol'], env=environment,
                           stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
rclpy.init()
probe = Node('pr04_defect_probe')
try:
    client = probe.create_client(GetParameters, '/patrol/get_parameters')
    assert client.wait_for_service(timeout_sec=20)
    response = subprocess.run(['timeout', '8s', 'ros2', 'param', 'set', '/patrol',
                               'publish_hz', '0.0'], capture_output=True, text=True, timeout=15)
    time.sleep(1)
    assert process.poll() is not None and process.returncode != 0
    log.flush()
    assert 'ZeroDivisionError' in (out / 'defect-patrol.txt').read_text()
    (out / 'defect.txt').write_text(
        '$ PYTHONPATH=/defect/src/patrol:$PYTHONPATH ros2 run patrol patrol\n'
        '$ timeout 8s ros2 param set /patrol publish_hz 0.0\n'
        + response.stdout + response.stderr + '\nCLI_EXIT=' + str(response.returncode)
        + '\nPATROL_EXIT=' + str(process.returncode) + '\n'
        + (out / 'defect-patrol.txt').read_text())
    print('PASS: bypassing frequency validation reproduces ZeroDivisionError; '
          'patrol exited with', process.returncode)
finally:
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGINT)
        process.wait(timeout=10)
    log.close()
    probe.destroy_node()
    rclpy.shutdown()
