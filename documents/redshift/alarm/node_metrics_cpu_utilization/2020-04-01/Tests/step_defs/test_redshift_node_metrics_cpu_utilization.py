# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/redshift_node_metrics_cpu_utilization.feature',
          'Create redshift:alarm:node_metrics_cpu_utilization:2020-04-01 based on '
          'CPUUtilization metric and check OK status.')
def test_node_metrics_cpu_utilization():
    pass
