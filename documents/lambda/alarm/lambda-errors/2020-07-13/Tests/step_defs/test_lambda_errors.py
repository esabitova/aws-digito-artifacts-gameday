# coding=utf-8
from pytest_bdd import (
    scenario
)

@scenario('../features/lambda_errors.feature',
          'Lease Lambda from resource manager and test attach an alarm from Document')
def test_lambda_errors():
    """Lease Lambda from resource manager and test attach an alarm from Document"""
    pass
