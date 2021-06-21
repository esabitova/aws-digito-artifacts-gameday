
from pytest_bdd import scenario


@scenario('../features/application_lb_network_unavailable_usual_case.feature',
          'Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01')
def test_application_lb_network_unavailable_usual_case():
    """Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01"""


@scenario('../features/application_lb_network_unavailable_rollback_previous.feature',
          'Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 in rollback')
def test_application_lb_network_unavailable_rollback_previous():
    """Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 in rollback"""


@scenario('../features/application_lb_network_unavailable_failed.feature',
          'Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 to test failure case')
def test_application_lb_network_unavailable_failed():
    """Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 to test failure case"""
