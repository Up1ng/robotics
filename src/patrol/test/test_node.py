# Copyright 2026 Gleb Neverov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Verify atomic validation, startup overrides and timer replacement in ROS."""

from patrol.patrol import Patrol
import pytest
import rclpy
from rclpy.parameter import Parameter


@pytest.fixture
def node():
    """Create an isolated node and release its context after each test."""
    rclpy.init()
    instance = Patrol()
    yield instance
    instance.destroy_node()
    rclpy.shutdown()


def test_timer_and_atomic_rejection(node):
    """A rejected mixed batch preserves settings and the sole active timer."""
    original = node.timer
    result = node.set_parameters_atomically([
        Parameter('linear_speed', value=0.9), Parameter('publish_hz', value=0.0)])
    assert not result.successful
    assert node.settings['linear_speed'] == 0.5
    assert node.get_parameter('linear_speed').value == 0.5
    assert node.timer is original
    assert node.timer.timer_period_ns == 100000000
    assert len(list(node.timers)) == 1
    result = node.set_parameters_atomically([Parameter('publish_hz', value=5.0)])
    assert result.successful
    assert node.timer is not original
    assert node.timer.timer_period_ns == 200000000
    assert len(list(node.timers)) == 1
    timer = node.timer
    assert node.set_parameters_atomically([Parameter('turn_rate', value=-1.0)]).successful
    assert node.timer is timer


def test_other_validator_rejection(node):
    """A later callback rejection cannot alter active state through side effects."""
    from rcl_interfaces.msg import SetParametersResult
    node.remove_on_set_parameters_callback(node.validate_update)
    node.add_on_set_parameters_callback(
        lambda parameters: SetParametersResult(successful=False, reason='test veto'))
    # New callbacks run first: validation succeeds, then the external veto runs.
    node.add_on_set_parameters_callback(node.validate_update)
    timer = node.timer
    assert not node.set_parameters_atomically([
        Parameter('publish_hz', value=5.0)]).successful
    assert node.timer is timer
    assert node.settings['publish_hz'] == 10.0


def test_bad_startup():
    """Reject an invalid command-line override before creating the timer."""
    rclpy.init(args=['--ros-args', '-p', 'publish_hz:=0.0'])
    try:
        with pytest.raises(ValueError, match='publish_hz'):
            Patrol()
    finally:
        rclpy.shutdown()
