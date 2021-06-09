from pytest_bdd import scenario


@scenario('../features/simulate_network_unavailable_usual_case.feature',
          'Execute SSM automation document Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21')
def test_simulate_network_unavailable_usual_case():
    """Execute SSM automation document Digito-RestApiGwSimulateNetworkUnavailable_2020-09-21"""
