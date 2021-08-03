
from pytest_bdd import scenario


@scenario('../features/application_lb_network_unavailable_usual_case.feature',
          'Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 usual case')
def test_application_lb_network_unavailable_usual_case():
    pass
