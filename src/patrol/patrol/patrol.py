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

"""Publish commands with validated parameters and a replaceable timer."""

from geometry_msgs.msg import Twist
from patrol.control import command_for_pose
from patrol.parameters import DEFAULTS, validate_parameters
from rcl_interfaces.msg import ParameterDescriptor, SetParametersResult
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from turtlesim.msg import Pose


class Patrol(Node):
    """Validate candidates first and apply only committed parameter batches."""

    def __init__(self):
        """Declare settings, validate startup overrides, then create ROS entities."""
        super().__init__('patrol')
        for name, value in DEFAULTS.items():
            self.declare_parameter(
                name, value, ParameterDescriptor(dynamic_typing=True))
        self.settings = {name: self.get_parameter(name).value for name in DEFAULTS}
        error = validate_parameters(self.settings)
        if error:
            self.destroy_node()
            raise ValueError(error)
        self.last_pose = None
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.subscription = self.create_subscription(Pose, 'pose', self.on_pose, 10)
        self.timer = self.create_timer(1.0 / self.settings['publish_hz'], self.on_timer)
        self.add_on_set_parameters_callback(self.validate_update)
        self.add_post_set_parameters_callback(self.apply_update)

    def validate_update(self, parameters):
        """Reject an entire batch without changing timer or active settings."""
        candidate = dict(self.settings)
        candidate.update({p.name: p.value for p in parameters if p.name in DEFAULTS})
        reason = validate_parameters(candidate)
        return SetParametersResult(successful=not reason, reason=reason)

    def apply_update(self, parameters):
        """Apply committed values; destroy the old timer when frequency changes."""
        candidate = dict(self.settings)
        candidate.update({p.name: p.value for p in parameters if p.name in DEFAULTS})
        if candidate['publish_hz'] != self.settings['publish_hz']:
            replacement = self.create_timer(1.0 / candidate['publish_hz'], self.on_timer)
            self.timer.cancel()
            self.destroy_timer(self.timer)
            self.timer = replacement
        self.settings = candidate

    def on_pose(self, message):
        """Store the latest pose for the next timer callback."""
        self.last_pose = message

    def on_timer(self):
        """Publish zero before receiving a pose, otherwise use current speeds."""
        self.publisher.publish(command_for_pose(
            self.last_pose, self.settings['linear_speed'], self.settings['turn_rate']))


def main(args=None):
    """Run in a single executor and release resources on shutdown."""
    rclpy.init(args=args)
    node = None
    try:
        node = Patrol()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
