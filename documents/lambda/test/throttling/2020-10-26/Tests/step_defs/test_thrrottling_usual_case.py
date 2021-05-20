# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/throttling_usual_case.feature',
          'Execute SSM automation document throttling')
def test_throttling():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
