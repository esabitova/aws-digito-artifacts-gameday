# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/elb_application_client_tls_negotiation_error_count.feature',
          'Alarm is not triggered when application ELB TLS error count is less than a threshold - green')
def test_application_elb_client_tls_negotiation_error_count_alarm():
    pass


@scenario('../features/elb_application_client_tls_negotiation_error_count.feature',
          'Alarm reports when application ELB TLS error count is greater or equal to a threshold - red')
def test_application_elb_client_tls_negotiation_error_count_exceeded_threshold_alarm():
    pass
