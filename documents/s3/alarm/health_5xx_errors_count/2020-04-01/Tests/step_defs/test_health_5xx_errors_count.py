# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_5xx_errors_count.feature',
          'Create the alarm based on the 5xxErrors metric')
def test_health_5xx_errors_count():
    pass
