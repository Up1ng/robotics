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

"""Check the complete command and that the policy has no side effects."""

from geometry_msgs.msg import Twist
from patrol.control import command_for_pose
from turtlesim.msg import Pose


def test_no_pose():
    """No received pose must produce a fully zero command."""
    assert command_for_pose(None) == Twist()


def test_received_pose():
    """A normal pose enables the fixed command and stays unchanged."""
    pose = Pose(x=5.0, y=4.0, theta=1.0)
    expected = Twist()
    expected.linear.x = 0.5
    expected.angular.z = 0.3
    assert command_for_pose(pose) == expected
    assert pose == Pose(x=5.0, y=4.0, theta=1.0)


def test_commands_do_not_share_state():
    """Mutating an earlier result must not affect later commands."""
    command = command_for_pose(Pose())
    command.linear.x = 9.0
    assert command_for_pose(Pose()).linear.x == 0.5
    assert command_for_pose(None) == Twist()
