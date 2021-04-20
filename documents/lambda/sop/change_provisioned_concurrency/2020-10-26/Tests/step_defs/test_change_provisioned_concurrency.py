# coding=utf-8
"""SSM automation document to change Lambda provisioned concurrency"""
from pytest_bdd import (
    scenario
)


@scenario('../features/change_provisioned_concurrency.feature',
          'Change provisioned concurrency of Lambda Function')
def test_change_provisioned_concurrency():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
