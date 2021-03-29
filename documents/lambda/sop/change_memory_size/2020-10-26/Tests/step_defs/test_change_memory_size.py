# coding=utf-8
"""SSM automation document to increase Lambda memory size"""
from pytest_bdd import (
    scenario
)


@scenario('../features/change_memory_size.feature',
          'Change memory size of Lambda Function')
def test_change_memory_size():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
