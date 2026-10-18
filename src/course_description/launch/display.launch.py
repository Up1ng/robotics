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

"""Expand the installed Xacro and display the tree with base_link as fixed frame."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Expose geometry and optional RViz without adding another tf publisher."""
    share = FindPackageShare('course_description')
    model = LaunchConfiguration('model')
    command = Command([
        FindExecutable(name='xacro'), ' ', model,
        ' wheelbase:=', LaunchConfiguration('wheelbase'),
        ' track:=', LaunchConfiguration('track'),
        ' wheel_radius:=', LaunchConfiguration('wheel_radius')])
    return LaunchDescription([
        DeclareLaunchArgument('model', default_value=PathJoinSubstitution(
            [share, 'urdf', 'vehicle.urdf.xacro'])),
        DeclareLaunchArgument('wheelbase', default_value='0.8'),
        DeclareLaunchArgument('track', default_value='0.62'),
        DeclareLaunchArgument('wheel_radius', default_value='0.12'),
        DeclareLaunchArgument('rviz', default_value='true', choices=['true', 'false']),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             name='robot_state_publisher', output='screen',
             parameters=[{'robot_description': ParameterValue(command, value_type=str)}]),
        Node(package='rviz2', executable='rviz2', name='rviz2', output='screen',
             arguments=['-d', PathJoinSubstitution([share, 'rviz', 'vehicle.rviz'])],
             condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
