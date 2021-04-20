# coding=utf-8
"""SSM automation document used to update provisioned capacity for DynamoDB Table."""

from pytest_bdd import (
    scenario
)


@scenario('../features/update_provisioned_capacity.feature',
          'Update provisioned capacity for DynamoDB Table')
def test_update_provisioned_capacity():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
