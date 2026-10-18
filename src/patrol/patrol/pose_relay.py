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

"""Relay the relative pose topic with a best-effort sensor QoS."""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from turtlesim.msg import Pose


class PoseRelay(Node):
    """Keep input names relative so launch controls remapping and namespace."""

    def __init__(self):
        """Create a reliable input and a best-effort output."""
        super().__init__('pose_relay')
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.publisher = self.create_publisher(Pose, 'sensor_pose', qos)
        self.subscription = self.create_subscription(Pose, 'pose', self.on_pose, 10)

    def on_pose(self, message):
        """Forward the unmodified message."""
        self.publisher.publish(message)


def main(args=None):
    """Spin until launch or the user stops the process."""
    rclpy.init(args=args)
    node = PoseRelay()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
