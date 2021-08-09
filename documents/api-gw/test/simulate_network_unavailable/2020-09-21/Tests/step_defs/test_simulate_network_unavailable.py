from pytest_bdd import scenario


@scenario('../features/simulate_network_unavailable_usual_case.feature',
          'Execute SSM automation document Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21 with provided '
          'security group')
def test_simulate_network_unavailable_usual_case_with_provided_security_group():
    """Execute SSM automation document Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21"""


@scenario('../features/simulate_network_unavailable_usual_case.feature',
          'Execute SSM automation document Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21 without provided '
          'security group')
def test_simulate_network_unavailable_usual_case_without_provided_security_group():
    """Execute SSM automation document Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21"""


@scenario('../features/simulate_network_unavailable_rollback_previous.feature',
          'Execute SSM automation document Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21 in rollback test')
def test_simulate_network_unavailable_rollback_case():
    """Execute SSM automation document Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21"""


@scenario('../features/simulate_network_unavailable_rollback_negative.feature',
          'Execute SSM automation document Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21 to test '
          'rollback failure when inputs different than original execution')
def test_simulate_network_unavailable_negative_rollback_case():
    """Execute SSM automation document Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21"""


@scenario('../features/simulate_network_unavailable_failed.feature',
          'Execute SSM automation document Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21 to test failure case')
def test_simulate_network_unavailable_failed_case():
    """Execute SSM automation document Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21"""


@scenario('../features/simulate_network_unavailable_failed.feature',
          'Execute SSM automation document Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21 to'
          ' test failure with wrong security group')
def test_simulate_network_unavailable_failed_case_with_provided_wrong_security_group():
    """Execute SSM automation document Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21"""
