# coding=utf-8
"""SSM automation document to scale down DocumentDb instances."""

from pytest_bdd import (
    scenario
)


@scenario('../features/scaling_down.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document' +
          ' for scaling down DocumentDb instances')
def test_scaling_down_docdb():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
