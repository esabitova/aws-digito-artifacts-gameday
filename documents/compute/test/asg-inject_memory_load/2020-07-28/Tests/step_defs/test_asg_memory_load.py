# coding=utf-8
"""SSM automation document for ASG memory injection. feature tests."""

import pytest
from pytest_bdd import (
    scenario
)


@pytest.mark.skip(reason="Broken test: https://issues.amazon.com/issues/Digito-2903")
@scenario('../features/asg_memory_load.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation document ASG memory stress')
def test_memory_stress_on_asg():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation document ASG memory stress."""
