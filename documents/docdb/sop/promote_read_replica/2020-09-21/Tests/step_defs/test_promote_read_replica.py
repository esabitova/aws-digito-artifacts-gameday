# coding=utf-8
"""SSM automation document for promoting DocDb replica to the primary instance."""

from pytest_bdd import (
    scenario
)


@scenario('../features/promote_read_replica.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document for promoting DocDb replica to the primary instance')
def test_promote_read_replica():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""