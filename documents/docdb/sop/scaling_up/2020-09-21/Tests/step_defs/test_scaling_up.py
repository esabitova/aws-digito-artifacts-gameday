# coding=utf-8
"""SSM automation document to scale up DocumentDb instances."""

from pytest_bdd import (
    scenario
)


@scenario('../features/scaling_up.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document'
          + ' for scaling up DocumentDb instances')
def test_scaling_up_docdb():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
