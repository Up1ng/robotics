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

"""Subscribe to turtlesim pose and publish a command every 0.1 seconds."""

from geometry_msgs.msg import Twist
from patrol.control import command_for_pose
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from turtlesim.msg import Pose


class Patrol(Node):
    """Keep the latest pose and let the timer choose the command."""

    def __init__(self):
        """Create the publisher, subscription and ten-hertz timer."""
        super().__init__('patrol')
        self.last_pose = None
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.subscription = self.create_subscription(
            Pose, '/turtle1/pose', self.on_pose, 10)
        self.timer = self.create_timer(0.1, self.on_timer)

    def on_pose(self, message):
        """Store the message; publishing belongs to the timer."""
        self.last_pose = message

    def on_timer(self):
        """Publish a new command selected from the latest pose."""
        self.publisher.publish(command_for_pose(self.last_pose))


def main(args=None):
    """Initialize ROS, process callbacks and release resources on Ctrl+C."""
    rclpy.init(args=args)
    node = Patrol()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
