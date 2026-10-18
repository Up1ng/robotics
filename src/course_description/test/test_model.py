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

"""Validate expanded geometry and semantic parents, beyond XML correctness."""

import math
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
import pytest


XACRO = os.environ.get('PR06_XACRO', str(
    Path(get_package_share_directory('course_description')) / 'urdf/vehicle.urdf.xacro'))


def expand(*arguments):
    """Use the real installed Xacro executable rather than a mock parser."""
    result = subprocess.run(['xacro', XACRO, *arguments],
                            capture_output=True, text=True, check=True)
    return ET.fromstring(result.stdout)


@pytest.fixture(scope='module')
def model():
    """Expand the default or intentionally defective model once."""
    return expand()


def vector(text):
    """Read a three-component vector in SI units."""
    return tuple(float(v) for v in text.split())


def test_connected_acyclic_tree(model):
    """Every child has exactly one parent and reaches the single base root."""
    names = [link.get('name') for link in model.findall('link')]
    assert len(names) == len(set(names))
    joints = model.findall('joint')
    assert len({j.get('name') for j in joints}) == len(joints)
    parents = {}
    for joint in joints:
        child = joint.find('child').get('link')
        parent = joint.find('parent').get('link')
        assert child not in parents
        assert parent in names and child in names
        parents[child] = parent
    assert set(names) - parents.keys() == {'base_link'}
    assert len(joints) == len(names) - 1
    for child in parents:
        seen = set()
        while child in parents:
            assert child not in seen, 'Cycle in joint tree'
            seen.add(child)
            child = parents[child]
        assert child == 'base_link'


def test_lidar_parent(model):
    """The fixed lidar offset is expressed in base_link, never in camera_link."""
    joint = model.find("joint[@name='lidar_joint']")
    assert joint.find('parent').get('link') == 'base_link'
    assert joint.get('type') == 'fixed'
    assert vector(joint.find('origin').get('xyz')) == pytest.approx((0.28, 0, 0.38))


@pytest.mark.parametrize('sensor', ['camera', 'lidar', 'imu'])
def test_sensor_mount_matches_sdf(model, sensor):
    """Use the provided model as input; compare each sensor's relative pose."""
    fixture = Path(__file__).resolve().parents[3] / (
        '.course-kit/v1/models/course_ackermann/model.sdf')
    sdf = ET.parse(fixture).getroot().find('model')
    expected = tuple(float(v) for v in sdf.find(
        f"link[@name='{sensor}_link']/pose").text.split()[:3])
    joint = model.find(f"joint[@name='{sensor}_joint']")
    assert joint.find('parent').get('link') == 'base_link'
    assert vector(joint.find('origin').get('xyz')) == pytest.approx(expected)


def test_optical_convention(model):
    """Camera optical frame uses z forward, x right and y down per REP-103."""
    joint = model.find("joint[@name='camera_optical_joint']")
    assert joint.find('parent').get('link') == 'camera_link'
    assert vector(joint.find('origin').get('rpy')) == pytest.approx(
        (-math.pi / 2, 0, -math.pi / 2))


def test_physical_elements(model):
    """Physical links have separate geometry and finite positive valid inertia."""
    for link in model.findall('link'):
        if link.get('name') == 'camera_optical_frame':
            continue
        assert link.find('visual/geometry') is not None
        assert link.find('collision/geometry') is not None
        mass = float(link.find('inertial/mass').get('value'))
        assert math.isfinite(mass) and mass > 0
        inertia = link.find('inertial/inertia').attrib
        assert all(math.isfinite(float(v)) for v in inertia.values())
        diagonal = [float(inertia[k]) for k in ('ixx', 'iyy', 'izz')]
        assert all(v > 0 for v in diagonal)
        assert all(float(inertia[k]) == 0 for k in ('ixy', 'ixz', 'iyz'))
        assert 2 * max(diagonal) <= sum(diagonal) + 1e-12
        for geometry in link.findall('*/geometry'):
            for shape in geometry:
                values = [float(v) for item in shape.attrib.values() for v in item.split()]
                assert all(math.isfinite(v) and 0 < v < 2 for v in values)


def test_default_chassis_dimensions(model):
    """Retain SDF body size, wheelbase, track and radius in metres."""
    assert vector(model.find("link[@name='base_link']/visual/geometry/box").get('size')) == (
        1.05, 0.52, 0.22)
    for side, sign in [('left', 1), ('right', -1)]:
        front = model.find(f"joint[@name='front_{side}_steering_joint']/origin")
        rear = model.find(f"joint[@name='rear_{side}_wheel_joint']/origin")
        assert vector(front.get('xyz')) == pytest.approx((0.4, sign * 0.31, 0))
        assert vector(rear.get('xyz')) == pytest.approx((-0.4, sign * 0.31, 0))
    for link in model.findall('link'):
        if link.get('name').endswith('_wheel'):
            assert float(link.find('visual/geometry/cylinder').get('radius')) == 0.12


def test_geometry_arguments():
    """A nondefault expansion must change both axles and every wheel shape."""
    altered = expand('wheelbase:=1.0', 'track:=0.7', 'wheel_radius:=0.15')
    for side, sign in [('left', 1), ('right', -1)]:
        front = altered.find(f"joint[@name='front_{side}_steering_joint']/origin")
        rear = altered.find(f"joint[@name='rear_{side}_wheel_joint']/origin")
        assert vector(front.get('xyz')) == pytest.approx((0.5, sign * 0.35, 0))
        assert vector(rear.get('xyz')) == pytest.approx((-0.5, sign * 0.35, 0))
    for link in altered.findall('link'):
        if link.get('name').endswith('_wheel'):
            assert float(link.find('collision/geometry/cylinder').get('radius')) == 0.15


def test_check_urdf(model, tmp_path):
    """Run the real structural checker on expanded XML."""
    path = tmp_path / 'vehicle.urdf'
    ET.ElementTree(model).write(path, encoding='unicode')
    result = subprocess.run(['check_urdf', str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert 'base_link' in result.stdout


def test_installed_launch():
    """Load the installed launch from a fresh CLI process."""
    result = subprocess.run(
        ['ros2', 'launch', 'course_description', 'display.launch.py', '--show-args'],
        capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert "'wheelbase'" in result.stdout and "'rviz'" in result.stdout
