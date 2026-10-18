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

"""Smoke-test the installed launch entry point from a new CLI process."""

import subprocess


def test_installed_launch_arguments():
    """Catch missing installed launch files or unresolved launch dependencies."""
    result = subprocess.run(
        ['ros2', 'launch', 'course_bringup', 'patrol.launch.py', '--show-args'],
        capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    for argument in ('namespace', 'record', 'bag_dir', 'subscriber_reliability'):
        assert "'" + argument + "'" in result.stdout
