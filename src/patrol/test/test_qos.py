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

"""Check the intended incompatibility using the ROS QoS compatibility API."""

from patrol.pose_subscriber import sensor_qos
import pytest
from rclpy.qos import qos_check_compatible, QoSCompatibility


def test_incompatible_then_fixed():
    """A best-effort offer fails reliable requests and accepts best effort."""
    publisher = sensor_qos('best_effort')
    assert qos_check_compatible(publisher, sensor_qos('reliable')).compatibility == (
        QoSCompatibility.ERROR)
    assert qos_check_compatible(publisher, sensor_qos('best_effort')).compatibility == (
        QoSCompatibility.OK)


def test_invalid_policy():
    """Reject typos instead of masking a configuration mistake."""
    with pytest.raises(ValueError):
        sensor_qos('best-effort')
