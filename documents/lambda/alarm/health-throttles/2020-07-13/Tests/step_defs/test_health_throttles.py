# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_throttles.feature',
          'Lease Lambda from resource manager and test attach an alarm from Document')
def test_lambda_throttles():
    """Lease Lambda from resource manager and test attach an alarm from Document"""
    pass
