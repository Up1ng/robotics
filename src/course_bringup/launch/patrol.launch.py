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

"""Launch one global simulator and a namespaced controller and sensor chain."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    """Resolve arguments at launch time, including the recorder condition."""
    namespace = LaunchConfiguration('namespace')
    record = LaunchConfiguration('record')
    bag_dir = LaunchConfiguration('bag_dir')
    reliability = LaunchConfiguration('subscriber_reliability')
    topic = PathJoinSubstitution(['/', namespace, 'sensor_pose'])
    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value='robot_a'),
        DeclareLaunchArgument('record', default_value='false', choices=['true', 'false']),
        DeclareLaunchArgument('bag_dir', default_value='evidence/pr05/bag'),
        DeclareLaunchArgument('subscriber_reliability', default_value='best_effort',
                              choices=['reliable', 'best_effort']),
        LogInfo(msg=['Starting namespace=', namespace, ', reliability=', reliability,
                     ', record=', record, ', bag=', bag_dir]),
        Node(package='turtlesim', executable='turtlesim_node', namespace='',
             output='screen'),
        Node(package='patrol', executable='patrol', namespace=namespace, output='screen',
             remappings=[('pose', '/turtle1/pose'), ('cmd_vel', '/turtle1/cmd_vel')]),
        Node(package='patrol', executable='pose_relay', namespace=namespace,
             output='screen', remappings=[('pose', '/turtle1/pose')]),
        Node(package='patrol', executable='pose_subscriber', namespace=namespace,
             output='screen', parameters=[{'reliability': reliability}]),
        ExecuteProcess(cmd=['ros2', 'bag', 'record', '-s', 'mcap', '-o', bag_dir,
                            '--topics', topic], output='screen',
                       condition=IfCondition(record)),
    ])
