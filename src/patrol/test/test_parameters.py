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

"""Check boundaries and rejection without an active graph."""

import math

from patrol.parameters import DEFAULTS, validate_parameters
import pytest


@pytest.mark.parametrize('name,value', [
    ('publish_hz', 0.0), ('publish_hz', -1.0), ('publish_hz', math.nan),
    ('publish_hz', math.inf), ('publish_hz', 30.1), ('publish_hz', True),
    ('publish_hz', '5'), ('linear_speed', -0.1), ('linear_speed', 1.1),
    ('linear_speed', math.nan), ('turn_rate', -1.1), ('turn_rate', 1.1),
    ('turn_rate', -math.inf),
])
def test_invalid(name, value):
    """Reject bad inputs and leave the candidate untouched."""
    candidate = dict(DEFAULTS, **{name: value})
    before = candidate.copy()
    assert validate_parameters(candidate)
    assert candidate == before


@pytest.mark.parametrize('hz', [1.0, 5.0, 10.0, 30.0])
def test_valid(hz):
    """Accept the frequency limits and the required ten-to-five transition."""
    assert validate_parameters(dict(DEFAULTS, publish_hz=hz)) == ''


def test_speed_boundaries():
    """Accept stationary motion and both turn directions at the limits."""
    for speed in (0.0, 1.0):
        for turn in (-1.0, 1.0):
            assert not validate_parameters(dict(DEFAULTS, linear_speed=speed, turn_rate=turn))
