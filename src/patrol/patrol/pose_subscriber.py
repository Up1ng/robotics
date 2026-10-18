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

"""Observe sensor poses with an explicitly selected reliability policy."""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from turtlesim.msg import Pose


def sensor_qos(reliability):
    """Validate the policy name rather than silently choosing a fallback."""
    policies = {'reliable': ReliabilityPolicy.RELIABLE,
                'best_effort': ReliabilityPolicy.BEST_EFFORT}
    if reliability not in policies:
        raise ValueError('reliability must be reliable or best_effort')
    return QoSProfile(depth=10, reliability=policies[reliability])


class PoseSubscriber(Node):
    """Log received counts so an incompatible connection is observable."""

    def __init__(self):
        """Read startup reliability and subscribe to the relative sensor topic."""
        super().__init__('pose_subscriber')
        policy = self.declare_parameter('reliability', 'best_effort').value
        self.count = 0
        self.subscription = self.create_subscription(
            Pose, 'sensor_pose', self.on_pose, sensor_qos(policy))
        self.timer = self.create_timer(1.0, self.report)
        self.get_logger().info(f'Subscriber reliability={policy}')

    def on_pose(self, message):
        """Count actual deliveries."""
        self.count += 1

    def report(self):
        """Publish a periodic diagnostic even when no messages arrive."""
        self.get_logger().info(f'received={self.count}')


def main(args=None):
    """Spin and clean up when replay or launch ends."""
    rclpy.init(args=args)
    node = None
    try:
        node = PoseSubscriber()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
