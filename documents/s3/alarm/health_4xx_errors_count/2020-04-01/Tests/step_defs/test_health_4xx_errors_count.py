# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/health_4xx_errors_count.feature',
          'Create the alarm based on the 4xxErrors metric')
def test_health_4xx_errors_count():
    pass
