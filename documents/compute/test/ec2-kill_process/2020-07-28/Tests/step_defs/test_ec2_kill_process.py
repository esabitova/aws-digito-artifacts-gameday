# coding=utf-8
"""SSM automation document for kill process in ec2 feature tests."""
import pytest
from pytest_bdd import (
    scenario
)


@pytest.mark.skip(reason="Broken test: https://issues.amazon.com/issues/Digito-2004")
@scenario('../features/ec2_kill_process.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation to kill process on ec2 instance')
def test_kill_process_on_ec2_instance():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation to kill process on ec2 instance."""


@pytest.mark.skip(reason="Broken test: https://issues.amazon.com/issues/Digito-2004")
@scenario('../features/ec2_kill_process.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation to kill process on ec2 instance, process does not exist')
def test_kill_process_on_ec2_instance_process_does_not_exist():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation to kill process on ec2 instance, process does not exist."""
