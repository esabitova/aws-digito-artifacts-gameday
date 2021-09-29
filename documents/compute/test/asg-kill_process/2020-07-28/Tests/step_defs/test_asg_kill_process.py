# coding=utf-8
"""SSM automation document for kill process in asg feature tests."""
import pytest
from pytest_bdd import (
    scenario
)


@pytest.mark.skip(reason="Broken test: https://issues.amazon.com/issues/Digito-2004")
@scenario('../features/asg_kill_process.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation to kill process on asg')
def test_kill_process_on_asg():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation to kill process on asg."""


@pytest.mark.skip(reason="Broken test: https://issues.amazon.com/issues/Digito-2004")
@scenario('../features/asg_kill_process.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation to kill process on asg, process does not exist')
def test_kill_process_on_asg_process_does_not_exist():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation to kill process on asg, process does not exist."""
