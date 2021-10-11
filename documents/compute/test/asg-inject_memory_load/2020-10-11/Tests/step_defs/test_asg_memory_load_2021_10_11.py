# coding=utf-8
"""SSM automation document for ASG memory injection. feature tests."""

import pytest
from pytest_bdd import (
    scenario
)


@scenario('../features/asg_memory_load_2021_10_11.feature',
          'Execute SSM automation document to perform memory stress injection on ASG')
def test_memory_stress_on_asg_2021_10_11():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation document ASG memory stress."""


@scenario('../features/asg_memory_load_2021_10_11.feature',
          'Execute SSM automation document to perform memory stress injection on ASG with rollback')
def test_memory_stress_on_asg_with_rollback_2021_10_11():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation document ASG memory stress."""
