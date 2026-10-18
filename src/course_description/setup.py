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

"""Install the robot model, launch and RViz configuration."""

from glob import glob

from setuptools import find_packages, setup

setup(
    name='course_description', version='0.0.0', packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/course_description']),
        ('share/course_description', ['package.xml']),
        ('share/course_description/urdf', glob('urdf/*.xacro')),
        ('share/course_description/launch', glob('launch/*.launch.py')),
        ('share/course_description/rviz', glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'], extras_require={'test': ['pytest']},
    zip_safe=True, maintainer='Gleb', maintainer_email='upingnev@gmail.com',
    description='Ackermann geometry, sensor frames and reproducible tf inspection.',
    license='Apache-2.0',
)
