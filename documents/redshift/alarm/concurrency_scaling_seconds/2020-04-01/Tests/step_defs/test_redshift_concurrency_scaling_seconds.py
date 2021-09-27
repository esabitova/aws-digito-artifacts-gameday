# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/redshift_concurrency_scaling_seconds.feature',
          'Create redshift:alarm:concurrency_scaling_seconds:2020-04-01 '
          'based on ConcurrencyScalingSeconds metric and check OK status')
def test_redshift_concurrency_scaling_seconds():
    pass
