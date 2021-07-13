# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/elb_application_target_tls_negotiation_error_count.feature',
          'Alarm is not triggered when target TLS negotiation error count is less than a threshold - green')
def test_elb_application_target_tls_negotiation_error_count_green():
    pass
