
from pytest_bdd import scenario


@scenario('../features/failover_usual_case.feature',
          'Execute SSM automation document Digito-FailoverElasticacheReplicationGroupTest_2020-10-26')
def test_failover_usual_case():
    """Execute SSM automation document Digito-FailoverElasticacheReplicationGroupTest_2020-10-26"""
