# coding=utf-8
"""SSM automation document for kill process in asg feature tests."""

from pytest_bdd import (
    scenario
)

from sttable import parse_str_table


@scenario('../features/asg_kill_process.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation to kill process on asg')
def test_kill_process_on_asg():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation to kill process on asg."""

@scenario('../features/asg_kill_process.feature',
          'Create AWS resources using CloudFormation template and execute '
          'SSM automation to kill process on asg, process does not exist')
def test_kill_process_on_asg_process_does_not_exist():
    """Create AWS resources using CloudFormation template and execute '
    'SSM automation to kill process on asg, process does not exist."""
