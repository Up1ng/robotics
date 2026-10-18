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

"""Validate a complete candidate without mutating ROS or active state."""

from math import isfinite


DEFAULTS = {'linear_speed': 0.5, 'turn_rate': 0.3, 'publish_hz': 10.0}
LIMITS = {'linear_speed': (0.0, 1.0), 'turn_rate': (-1.0, 1.0),
          'publish_hz': (1.0, 30.0)}


def validate_parameters(values):
    """Return an error for nonfinite, out-of-range or nonnumeric settings."""
    for name, (lower, upper) in LIMITS.items():
        if name == 'publish_hz':
            continue  # Intentional PR04 defect: bypass frequency validation.
        value = values[name]
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not isfinite(value) or not lower <= value <= upper):
            return f'{name} must be finite and in [{lower}, {upper}]'
    return ''
