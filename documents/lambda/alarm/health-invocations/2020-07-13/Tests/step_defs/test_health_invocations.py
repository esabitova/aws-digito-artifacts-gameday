# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_invocations.feature',
          'Lease Lambda from resource manager and test attach an alarm from Document')
def test_lambda_invocations():
    """Lease Lambda from resource manager and test attach an alarm from Document"""
    pass
