# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/promote_non_aurora_replica.feature', 'Create AWS resources using CloudFormation template '
          'and execute SSM automation document to promote non aurora replica')
def test_promote_non_aurora_replica():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
