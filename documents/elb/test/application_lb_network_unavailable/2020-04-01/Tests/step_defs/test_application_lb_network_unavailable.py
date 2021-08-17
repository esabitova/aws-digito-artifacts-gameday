
from pytest_bdd import scenario


@scenario('../features/application_lb_network_unavailable_usual_case.feature',
          'Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 usual case')
def test_application_lb_network_unavailable_usual_case():
    pass


@scenario('../features/application_lb_network_unavailable_usual_case.feature',
          'Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 with '
          'SecurityGroupIdsToDelete param specified')
def test_application_lb_network_unavailable_sg_ids_specified():
    pass


@scenario('../features/application_lb_network_unavailable_failed.feature',
          'Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 to test failure case')
def test_application_lb_network_unavailable_failure_case():
    pass


@scenario('../features/application_lb_network_unavailable_failed.feature',
          'Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 '
          'with SecurityGroupIdsToDelete param specified to test failure case')
def test_application_lb_network_unavailable_with_param_specified_failure_case():
    pass


@scenario('../features/application_lb_network_unavailable_rollback_previous.feature',
          'Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 in rollback')
def test_application_lb_network_unavailable_automation_rollback():
    pass
